import socket
import sys

host = "db.jgmqmvfdetyxibzeleuz.supabase.co"
port = 5432

print(f"Testing connection to {host}:{port}...")

try:
    # DNS Resolution
    ip = socket.gethostbyname(host)
    print(f"DNS Resolved: {ip}")
    
    # TCP Connection
    s = socket.create_connection((host, port), timeout=10)
    print("TCP Connection Successful!")
    s.close()
except Exception as e:
    print(f"Connection Failed: {e}")
