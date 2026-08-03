"""Build the recap email body.

THREE HARD CONSTRAINTS, all load-bearing:

1. NO NEWLINES. EMAIL.email does `body = body.replace("\\n", "<br>")` before
   handing the string to Outlook. A pretty-printed template would fill the mail
   with stray <br>. Everything is joined from a list; `assert_sendable()` is the
   backstop.

2. NO `border-left` (or border-left-color/style/width) -- CLAUDE.md hard rule
   across all HTML/CSS. A bar chart's baseline axis is the single likeliest
   place to reach for it. Note the usual substitute, `box-shadow: inset`, is
   IGNORED by Outlook's Word rendering engine, so separators here are literal
   1px <td bgcolor> spacer cells instead.

3. NO <style> BLOCK AND NO JS. Outlook strips the former and never runs the
   latter, so every rule is inlined per element and the chart is built from
   nested tables with percentage widths -- which also makes it immune to the
   image-blocking that would kill a rendered PNG.
"""

import re


# OUTPUT.py THEMES["console_dark"], inlined as literals because <style> is stripped.
THEME = {
    "surface": "#1e1e1e",
    "text_primary": "#cccccc",
    "text_muted": "#8a8a8a",
    "heading_primary": "#e8e8e8",
    "heading_secondary": "#9cdcfe",
    "link": "#4ec9b0",
    "footer_muted": "#808080",
    "accent": "#d97706",
    "accent_strong": "#fbbf24",
    "font_family": "Consolas, 'Courier New', monospace",
}

BODY_WIDTH = 600
_BORDER_LEFT = re.compile(r"border-left", re.IGNORECASE)


def esc(text):
    """Minimal HTML escape. Tool names and docs are author-controlled but the
    recap also renders raw log keys, which are not."""
    return (
        str(text if text is not None else "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _one_line(text):
    """Collapse anything that could introduce a newline into the body."""
    return " ".join(str(text or "").split())


# ------------------------------------------------------------------ bar chart

def bar_chart(series, highlight=None, max_bars=6):
    """Table-based horizontal bar chart. No images, no CSS that Outlook drops.

    `series` is [{"label": str, "value": number}]. `highlight` is an index
    drawn in the accent colour.
    """
    rows = [item for item in (series or []) if item.get("value") is not None][:max_bars]
    if not rows:
        return ""
    peak = max(float(item["value"]) for item in rows) or 1.0

    parts = [
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        'width="100%" style="border-collapse:collapse;width:100%;">'
    ]
    for index, item in enumerate(rows):
        value = float(item["value"])
        pct = max(1, int(round((value / peak) * 100)))
        colour = THEME["accent"] if index == highlight else THEME["heading_secondary"]
        weight = "bold" if index == highlight else "normal"
        parts.append(
            '<tr>'
            '<td width="180" style="padding:4px 8px 4px 0;font-family:{font};'
            'font-size:12px;color:{text};font-weight:{weight};text-align:right;'
            'vertical-align:middle;">{label}</td>'
            '<td style="padding:4px 0;vertical-align:middle;">'
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
            'width="{pct}%" style="border-collapse:collapse;">'
            '<tr><td height="14" bgcolor="{colour}" '
            'style="height:14px;font-size:0;line-height:0;border-radius:2px;">&nbsp;</td>'
            '</tr></table></td>'
            '<td width="56" style="padding:4px 0 4px 8px;font-family:{font};'
            'font-size:12px;color:{muted};vertical-align:middle;">{value}</td>'
            '</tr>'.format(
                font=THEME["font_family"],
                text=THEME["text_primary"],
                muted=THEME["text_muted"],
                colour=colour,
                weight=weight,
                pct=pct,
                label=esc(_one_line(item.get("label"))),
                value=esc(_format_number(value)),
            )
        )
    parts.append("</table>")
    return "".join(parts)


def _format_number(value):
    if abs(value - round(value)) < 0.05:
        return "{:,}".format(int(round(value)))
    return "{:,.1f}".format(value)


# --------------------------------------------------------------------- pieces

def _rule():
    """Horizontal separator. A literal spacer cell, because Outlook ignores
    box-shadow and border-left is banned outright."""
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        'width="100%"><tr><td height="1" bgcolor="#3a3a3a" '
        'style="height:1px;font-size:0;line-height:0;">&nbsp;</td></tr></table>'
    )


def _heading(text, size=20, colour=None):
    return (
        '<div style="font-family:{font};font-size:{size}px;font-weight:bold;'
        'color:{colour};margin:0 0 10px 0;line-height:1.35;">{text}</div>'.format(
            font=THEME["font_family"], size=size,
            colour=colour or THEME["heading_primary"], text=esc(_one_line(text)))
    )


def _paragraph(text, colour=None, size=14):
    return (
        '<div style="font-family:{font};font-size:{size}px;color:{colour};'
        'margin:0 0 14px 0;line-height:1.55;">{text}</div>'.format(
            font=THEME["font_family"], size=size,
            colour=colour or THEME["text_primary"], text=esc(_one_line(text)))
    )


def _stat_row(stats):
    cells = []
    width = int(100 / max(1, len(stats)))
    for label, value in stats:
        cells.append(
            '<td width="{w}%" align="center" style="padding:12px 6px;">'
            '<div style="font-family:{font};font-size:22px;font-weight:bold;'
            'color:{accent};">{value}</div>'
            '<div style="font-family:{font};font-size:11px;color:{muted};'
            'text-transform:uppercase;letter-spacing:0.5px;padding-top:4px;">{label}</div>'
            '</td>'.format(w=width, font=THEME["font_family"],
                           accent=THEME["accent_strong"], muted=THEME["text_muted"],
                           value=esc(value), label=esc(label))
        )
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        'width="100%" style="border-collapse:collapse;"><tr>'
        + "".join(cells) + "</tr></table>"
    )


def _recommendation(index, tool):
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        'width="100%" style="border-collapse:collapse;margin:0 0 10px 0;">'
        '<tr>'
        '<td width="4" bgcolor="{accent}" style="width:4px;font-size:0;line-height:0;">&nbsp;</td>'
        '<td style="padding:8px 0 8px 12px;">'
        '<div style="font-family:{font};font-size:14px;font-weight:bold;color:{head};">'
        '{index}. {name}</div>'
        '<div style="font-family:{font};font-size:12px;color:{muted};padding-top:3px;'
        'line-height:1.5;">{doc}</div>'
        '<div style="font-family:{font};font-size:11px;color:{footer};padding-top:4px;">'
        '{app} &middot; {tab}</div>'
        '</td></tr></table>'.format(
            accent=THEME["accent"], font=THEME["font_family"],
            head=THEME["heading_primary"], muted=THEME["text_primary"],
            footer=THEME["footer_muted"], index=index,
            name=esc(_one_line(tool.get("alias"))),
            doc=esc(_one_line(tool.get("doc_line") or "")),
            app=esc(tool.get("app") or ""), tab=esc(tool.get("tab") or ""))
    )


# ----------------------------------------------------------------------- body

def build(claim, metrics, recommendations, user_name, opt_out_hint=None):
    """The full HTML body. Single line, inline-styled, no JS."""
    month = metrics["month"]
    parts = []

    parts.append(
        '<div style="background-color:{bg};padding:24px 0;font-family:{font};">'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        'width="{w}" align="center" style="width:{w}px;max-width:100%;'
        'border-collapse:collapse;background-color:{bg};"><tr><td style="padding:0 24px;">'
        .format(bg=THEME["surface"], font=THEME["font_family"], w=BODY_WIDTH)
    )

    # Headline: gapped surface, then the resolution immediately beneath it.
    if claim is not None:
        parts.append(_heading(claim.render_surface(), size=20))
        parts.append(_paragraph(claim.render_body(), colour=THEME["text_primary"]))
        chart = getattr(claim, "chart", None) or {}
        if chart.get("series"):
            parts.append(_paragraph(chart.get("title", ""),
                                    colour=THEME["text_muted"], size=12))
            parts.append(bar_chart(chart["series"], chart.get("highlight")))
            parts.append('<div style="height:18px;font-size:0;">&nbsp;</div>')

    parts.append(_rule())

    # Your month, in numbers.
    parts.append('<div style="height:6px;font-size:0;">&nbsp;</div>')
    parts.append(_stat_row([
        ("Runs", "{:,}".format(month.get("total_runs", 0))),
        ("Active days", str(month.get("active_days", 0))),
        ("Tools used", str(month.get("distinct_tools", 0))),
        ("Hours", "{:.1f}".format(month.get("seconds_in_tools", 0.0) / 3600.0)),
    ]))

    # Top tools chart.
    top = month.get("top_tools") or []
    if top:
        display = []
        for key, count in top[:6]:
            display.append({"label": _pretty_key(key, metrics), "value": count})
        parts.append('<div style="height:10px;font-size:0;">&nbsp;</div>')
        parts.append(_heading("What you reached for most", size=15))
        parts.append(bar_chart(display, highlight=0))
        parts.append('<div style="height:20px;font-size:0;">&nbsp;</div>')

    # Recommendations.
    if recommendations:
        parts.append(_rule())
        parts.append('<div style="height:14px;font-size:0;">&nbsp;</div>')
        parts.append(_heading("Three you haven't opened", size=15))
        for index, tool in enumerate(recommendations, start=1):
            parts.append(_recommendation(index, tool))

    # Footer -- an unsubscribe you have to ask a human for is what gets mail
    # marked as spam.
    parts.append('<div style="height:16px;font-size:0;">&nbsp;</div>')
    parts.append(_rule())
    parts.append(
        '<div style="font-family:{font};font-size:11px;color:{muted};'
        'padding-top:12px;line-height:1.6;">{hint}</div>'.format(
            font=THEME["font_family"], muted=THEME["footer_muted"],
            hint=esc(_one_line(opt_out_hint or
                     "Turn this off any time: EnneadTab > Setting > Emails > "
                     "Monthly EnneadTab usage recap.")))
    )

    parts.append("</td></tr></table></div>")

    body = "".join(parts)
    assert_sendable(body)
    return body


def _pretty_key(tool_key, metrics):
    """Title-case a normalized log key for display when no catalog name exists."""
    names = metrics.get("display_names") or {}
    if tool_key in names:
        return names[tool_key]
    return " ".join(word.capitalize() for word in str(tool_key).split())


# ------------------------------------------------------------------ guardrails

def assert_sendable(body):
    """Fail loudly rather than send a corrupted or rule-violating body."""
    if "\n" in body or "\r" in body:
        raise ValueError(
            "Recap body contains a newline. EMAIL.email replaces \\n with <br>, "
            "which would corrupt the layout. Join fragments instead."
        )
    if _BORDER_LEFT.search(body):
        raise ValueError(
            "Recap body uses border-left, which is banned repo-wide (CLAUDE.md). "
            "Use a 1px <td bgcolor> spacer cell instead."
        )
    if "<style" in body.lower():
        raise ValueError("Outlook strips <style> blocks; inline every rule instead.")
    return True
