import socket
import ssl
import pg8000.native

# IPv6 from nslookup
HOST_IP = "2600:1f18:2e13:9d30:b5e1:a957:96d3:df6"
HOST_NAME = "db.jgmqmvfdetyxibzeleuz.supabase.co"
PORT = 5432
USER = "postgres"
PASS = "X03T25mqUB9ZmL8Q"
DB = "postgres"

def test_direct_ipv6():
    print(f"Testing direct connection to [{HOST_IP}]:{PORT}...")
    try:
        # Create a socket explicitly for IPv6
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((HOST_IP, PORT))
        print("  [SUCCESS] TCP Connection established!")
        s.close()
        
        # Now try pg8000
        print("\nTesting pg8000 with IPv6 IP...")
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        conn = pg8000.native.Connection(
            user=USER,
            password=PASS,
            host=HOST_IP, # Using IP directly
            port=PORT,
            database=DB,
            ssl_context=ssl_context,
            timeout=10
        )
        print("  [SUCCESS] pg8000 Connected!")
        conn.close()
        
    except Exception as e:
        print(f"  [FAIL] Error: {e}")

if __name__ == "__main__":
    test_direct_ipv6()
