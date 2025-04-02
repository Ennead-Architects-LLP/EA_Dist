import socket
import sys
import os
import argparse

# Add the Apps directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.EnneadTab import WEB

def check_server_status(host, port):
    """Check if server is reachable and port is open."""
    try:
        # Create a socket object
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        
        # Try to connect
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f"Server {host}:{port} is reachable and port is open")
            return True
        else:
            print(f"Server {host}:{port} is reachable but port is closed")
            return False
        
        sock.close()
    except socket.error as e:
        print(f"Error checking server status: {e}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', action='store_true', help='Run in server mode')
    args = parser.parse_args()

    if args.server:
        print("Starting server mode...")
        WEB.start_server()
        return

    # Client mode
    current_fqdn = socket.getfqdn()
    print(f"Current computer's full address: {current_fqdn}")
    
    # Extract domain and construct server address
    domain = current_fqdn.split('.', 1)[1] if '.' in current_fqdn else None
    server_address = f"SZHANG.{domain}" if domain else "SZHANG"
    print(f"Attempting to connect to server at: {server_address}")
    
    # Try a few common ports
    ports_to_try = [12345, 8080, 5000]
    for port in ports_to_try:
        print(f"\nTrying port {port}...")
        if check_server_status(server_address, port):
            print(f"Found open port at {port}, attempting connection...")
            WEB.call_me(server_ip=server_address, port=port)
            return
    
    print("\nNo open ports found. Please ensure the server is running.")

if __name__ == "__main__":
    main() 