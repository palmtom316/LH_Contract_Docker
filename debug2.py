import urllib.request
import urllib.parse
import json

# Login
login_data = urllib.parse.urlencode({"username": "admin", "password": "admin123"}).encode()
req = urllib.request.Request("http://localhost:8000/api/v1/auth/login", data=login_data, method="POST")
req.add_header("Content-Type", "application/x-www-form-urlencoded")

with urllib.request.urlopen(req) as response:
    token = json.loads(response.read().decode())["access_token"]
    print(f"✓ Logged in")

# Create a contract with serial_number 14  
contract_data = {
    "serial_number": 14,
    "contract_code": "DEBUG-TEST-002",
    "contract_name": "调试测试合同2",
    "party_a_name": "甲方公司",
    "party_b_name": "乙方公司",
    "contract_amount": 100000.00,
    "sign_date": "2025-12-15",
    "category": "GENERAL",
    "company_category": "测试分类",
    "pricing_mode": "FIXED_TOTAL",
    "management_mode": "SELF",
    "responsible_person": "测试人",
    "status": "执行中"
}

req = urllib.request.Request("http://localhost:8000/api/v1/contracts/upstream/", method="POST")
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Content-Type", "application/json")

try:
    print("Sending request...")
    with urllib.request.urlopen(req, data=json.dumps(contract_data).encode()) as response:
        print(f"Response status: {response.getcode()}")
        body = response.read().decode()
        print(f"Response body length: {len(body)}")
        result = json.loads(body)
        print(f"✓ Success! Created contract ID: {result.get('id')}")
        print(f"  Contract: {result.get('contract_name')}")
except urllib.error.HTTPError as e:
    print(f"✗ HTTP Error {e.code}")
    error_body = e.read().decode('utf-8', errors='replace')
    print(f"Full error response ({len(error_body)} bytes):")
    print(error_body)
    print("\n---END OF ERROR RESPONSE---")
except Exception as e:
    print(f"✗ Exception: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
