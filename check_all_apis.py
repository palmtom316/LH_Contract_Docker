import urllib.request
import urllib.parse
import json
import ssl

BASE_URL = "http://localhost:8000/api/v1"

def check_apis():
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        # 1. Login
        print("Logging in...")
        login_data = urllib.parse.urlencode({"username": "admin", "password": "admin123"}).encode()
        req = urllib.request.Request(f"{BASE_URL}/auth/login", data=login_data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        
        token = ""
        with urllib.request.urlopen(req, context=ctx) as response:
            if response.status != 200:
                print(f"Login failed: {response.status}")
                return
            response_body = response.read().decode()
            token = json.loads(response_body)["access_token"]
            
        # 2. Check Downstream
        print("Checking Downstream Contracts...")
        req = urllib.request.Request(f"{BASE_URL}/contracts/downstream/?skip=0&limit=10", method="GET")
        req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, context=ctx) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    items = data.get("items", [])
                    print(f"  Downstream Count: {len(items)}")
                    if items: print(f"  First: {items[0].get('contract_name')}")
                else:
                    print(f"  Failed: {response.status}")
        except Exception as e:
            print(f"  Error Downstream: {e}")

        # 3. Check Management
        print("Checking Management Contracts...")
        req = urllib.request.Request(f"{BASE_URL}/contracts/management/?skip=0&limit=10", method="GET")
        req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, context=ctx) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    items = data.get("items", [])
                    print(f"  Management Count: {len(items)}")
                    if items: print(f"  First: {items[0].get('contract_name')}")
                else:
                    print(f"  Failed: {response.status}")
        except Exception as e:
            print(f"  Error Management: {e}")

    except Exception as e:
        print(f"Fatal Error: {e}")

if __name__ == "__main__":
    check_apis()
