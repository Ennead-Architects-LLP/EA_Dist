"""HTTP server for the MCP chat web UI.

Serves the chat page and proxies LLM API calls with tool execution.
Uses stdlib only (http.server + urllib).
"""

from __future__ import annotations

import json
import os
import sys
import threading
import urllib.request
import urllib.error
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List, Optional

from . import llm_client
from .web_ui import get_index_html

# EnneadTabHome endpoint for centralized API keys
_KEYS_URL = "https://enneadtab.com/api/keys/llm"


def _fetch_central_keys() -> Dict[str, Dict[str, str]]:
    """Fetch LLM API keys from EnneadTabHome.

    Uses DEBUG_BYPASS_SECRET for auth (set on the Vercel project).
    Falls back to environment variables if the fetch fails.
    """
    providers = {}

    # Try central endpoint first
    bypass = os.environ.get("DEBUG_BYPASS_SECRET", "")
    if bypass:
        try:
            req = urllib.request.Request(_KEYS_URL, method="GET")
            req.add_header("x-debug-bypass", bypass)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                providers = data.get("providers", {})
        except Exception:
            pass

    # Fallback to local environment variables
    if "anthropic" not in providers:
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if key:
            providers["anthropic"] = {"key": key, "model": "claude-sonnet-4-20250514"}

    if "gemini" not in providers:
        key = os.environ.get("GOOGLE_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
        if key:
            providers["gemini"] = {"key": key, "model": "gemini-2.0-flash"}

    return providers


def _execute_tool(tools: Dict[str, Any], name: str, arguments: Dict) -> Any:
    """Execute a registered MCP tool by name."""
    entry = tools.get(name)
    if not entry:
        raise ValueError("Unknown tool: {}".format(name))
    return entry["handler"](**arguments)


def _get_tool_list(tools: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get MCP tool definitions for the LLM API."""
    result = []
    for name, entry in tools.items():
        result.append({
            "name": name,
            "description": entry.get("description", ""),
            "inputSchema": entry.get("parameters", {"type": "object", "properties": {}}),
        })
    return result


def make_handler(tools: Dict[str, Any], providers: Dict[str, Dict[str, str]], port: int):
    """Create a request handler class with tool and provider context."""

    class ChatHandler(BaseHTTPRequestHandler):

        def do_GET(self):
            # Parse path and query string
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)

            if path == "/":
                html = get_index_html().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html)))
                self.end_headers()
                self.wfile.write(html)

            elif path == "/api/health":
                # Report which providers are available (without exposing keys)
                available = {}
                for k, v in providers.items():
                    available[k] = {"model": v.get("model", "")}
                has_keys = len(available) > 0
                body = json.dumps({
                    "status": "ok",
                    "providers": available,
                    "has_keys": has_keys,
                    "auth_url": "https://enneadtab.com/api/keys/llm-auth?port={}".format(port),
                }).encode()
                self._json_response(200, body)

            elif path == "/api/tools":
                tool_list = [{"name": n, "description": e.get("description", "")}
                             for n, e in tools.items()]
                body = json.dumps({"tools": tool_list}).encode()
                self._json_response(200, body)

            elif path == "/api/auth/callback":
                # Handle redirect callback from EnneadTabHome with API keys
                token = query.get("token", [""])[0]
                if not token:
                    self.send_error(400, "Missing token")
                    return
                try:
                    import base64
                    payload = json.loads(base64.urlsafe_b64decode(token + "=="))
                    new_providers = payload.get("providers", {})
                    # Merge into the shared providers dict
                    providers.update(new_providers)
                    user_email = payload.get("user", "unknown")
                    print("[web] Auth callback: {} ({} providers)".format(
                        user_email, len(new_providers)), file=sys.stderr)
                    # Redirect to chat page
                    self.send_response(302)
                    self.send_header("Location", "/")
                    self.end_headers()
                except Exception as e:
                    self.send_error(400, "Invalid token: {}".format(e))

            else:
                self.send_error(404)

        def do_POST(self):
            if self.path == "/api/chat":
                self._handle_chat()
            else:
                self.send_error(404)

        def do_OPTIONS(self):
            self.send_response(200)
            self._cors_headers()
            self.end_headers()

        def _handle_chat(self):
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length)
                data = json.loads(raw.decode("utf-8"))
            except Exception as e:
                self._json_response(400, json.dumps({"error": "Bad request: {}".format(e)}).encode())
                return

            messages = data.get("messages", [])
            provider = data.get("provider", "")
            manual_key = data.get("manual_key", "")

            if not provider or not messages:
                self._json_response(400, json.dumps({"error": "Missing provider or messages"}).encode())
                return

            # Resolve API key: central > manual > none
            prov_info = providers.get(provider, {})
            api_key = prov_info.get("key", "")
            if not api_key and manual_key:
                api_key = manual_key

            if not api_key:
                self._json_response(400, json.dumps({"error": "No API key for {}".format(provider)}).encode())
                return

            mcp_tools = _get_tool_list(tools)

            execute = lambda name, args: _execute_tool(tools, name, args)

            # Try primary provider, auto-fallback to the other on failure
            fallback_provider = "gemini" if provider == "anthropic" else "anthropic"
            fallback_info = providers.get(fallback_provider, {})
            fallback_key = fallback_info.get("key", "")

            try:
                result = llm_client.run_chat(
                    provider=provider,
                    api_key=api_key,
                    messages=messages,
                    mcp_tools=mcp_tools,
                    execute_fn=execute,
                )
                result["provider_used"] = provider
                body = json.dumps(result).encode()
                self._json_response(200, body)
            except Exception as primary_err:
                # Auto-fallback to other provider
                if fallback_key:
                    try:
                        result = llm_client.run_chat(
                            provider=fallback_provider,
                            api_key=fallback_key,
                            messages=messages,
                            mcp_tools=mcp_tools,
                            execute_fn=execute,
                        )
                        result["provider_used"] = fallback_provider
                        result["fallback_reason"] = str(primary_err)[:200]
                        body = json.dumps(result).encode()
                        self._json_response(200, body)
                        return
                    except Exception:
                        pass

                # Both failed — report primary error
                if isinstance(primary_err, urllib.error.HTTPError):
                    error_body = ""
                    try:
                        error_body = primary_err.read().decode("utf-8", errors="replace")
                    except Exception:
                        pass
                    msg = "LLM API error {}: {}".format(primary_err.code, error_body[:500])
                else:
                    msg = str(primary_err)
                self._json_response(502, json.dumps({"error": msg}).encode())

        def _json_response(self, code: int, body: bytes):
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self._cors_headers()
            self.end_headers()
            self.wfile.write(body)

        def _cors_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def log_message(self, format, *args):
            print("[web] " + (format % args), file=sys.stderr)

    return ChatHandler


def start_web_server(
    mcp_tools: Dict[str, Any],
    host: str = "127.0.0.1",
    port: int = 5000,
    open_browser: bool = True,
) -> None:
    """Start the web chat server.

    Args:
        mcp_tools: Tool registry dict from McpServer._tools
        host: Bind address
        port: Port number
        open_browser: Auto-open browser on start
    """
    print("Fetching API keys...", file=sys.stderr)
    providers = _fetch_central_keys()
    if providers:
        print("Available providers: {}".format(", ".join(providers.keys())), file=sys.stderr)
    else:
        print("WARNING: No API keys found. Users must provide keys manually.", file=sys.stderr)

    handler_class = make_handler(mcp_tools, providers, port)

    # Try the requested port, fall back to next available
    for attempt_port in range(port, port + 10):
        try:
            httpd = HTTPServer((host, attempt_port), handler_class)
            break
        except OSError:
            continue
    else:
        print("ERROR: Could not bind to any port in range {}-{}".format(port, port + 9), file=sys.stderr)
        sys.exit(1)

    actual_port = attempt_port
    url = "http://{}:{}".format(host, actual_port)
    print("Web UI: {}".format(url), file=sys.stderr)

    if open_browser:
        threading.Timer(0.5, webbrowser.open, args=[url]).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down web server.", file=sys.stderr)
        httpd.shutdown()
