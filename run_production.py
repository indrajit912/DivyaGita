import os
import socket
from dotenv import load_dotenv
from waitress import serve
from app import create_app

# 1. Load environment variables from .env file
load_dotenv()

# 2. Enforce production environment settings
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = '0'

# 3. Create the production application instance
app = create_app('production')

def get_local_ip():
    """Retrieve the active local network interface IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Using a dummy public destination to determine routing interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == '__main__':
    # Bind to 0.0.0.0 by default to allow access from other devices on the network
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    
    local_ip = get_local_ip()
    
    print("\n-------------------------------------------------------------")
    print("Starting DivyaGita production server...")
    print(f"  > Local (Host):     http://127.0.0.1:{port}")
    if host == '0.0.0.0' and local_ip != '127.0.0.1':
        print(f"  > Network (LAN):    http://{local_ip}:{port}")
    print("Serving with production-grade Waitress engine (8 threads)...")
    print("-------------------------------------------------------------\n")
    
    # Start serving requests
    serve(app, host=host, port=port, threads=8)
