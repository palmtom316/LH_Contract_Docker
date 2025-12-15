import urllib.request
import urllib.parse
import json
import ssl

BASE_URL = "http://localhost:8000/api/v1"

def check_data():
    try:
        # Create a context that doesn't verify SSL (just in case, though for localhost http it's fine)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        # 1. Login
        login_data = urllib.parse.urlencode({"username": "admin", "password": "admin123"}).encode()
        req = urllib.request.Request(f"{BASE_URL}/auth/login", data=login_data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        
        with urllib.request.urlopen(req, context=ctx) as response:
            if response.status != 200:
                print(f"Login failed: {response.status}")
                return
            response_body = response.read().decode()
            token = json.loads(response_body)["access_token"]
            
        # 2. Get Upstream Contracts
        req = urllib.request.Request(f"{BASE_URL}/contracts/upstream/?skip=0&limit=100", method="GET")
        req.add_header("Authorization", f"Bearer {token}")
        
        with urllib.request.urlopen(req, context=ctx) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                # Should be a list or pagination dict
                items = data.get("items", []) if isinstance(data, dict) else data
                print(f"Upstream Contracts API Count: {len(items)}")
                if len(items) > 0:
                    print(f"First contract: {items[0].get('contract_name', 'Unknown')}")
            else:
                print(f"Failed to get contracts: {response.status}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_data()
