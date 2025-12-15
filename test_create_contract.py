import urllib.request
import urllib.parse
import json

# Login
login_data = urllib.parse.urlencode({"username": "admin", "password": "admin123"}).encode()
req = urllib.request.Request("http://localhost:8000/api/v1/auth/login", data=login_data, method="POST")
req.add_header("Content-Type", "application/x-www-form-urlencoded")

with urllib.request.urlopen(req) as response:
    token = json.loads(response.read().decode())["access_token"]

# Try to create a new upstream contract
contract_data = {
    "serial_number": 11,
    "contract_code": "TEST-20251215-001",
    "contract_name": "测试合同",
    "party_a_name": "甲方公司",
    "party_b_name": "乙方公司",
    "contract_amount": 100000.00,
    "sign_date": "2025-12-15",
    "category": "GENERAL",  # Use English enum value, not Chinese
    "company_category": "市区配网",
    "pricing_mode": "FIXED_TOTAL",
    "management_mode": "SELF",
    "status": "执行中"
}

req = urllib.request.Request("http://localhost:8000/api/v1/contracts/upstream/", method="POST")
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Content-Type", "application/json")

try:
    with urllib.request.urlopen(req, data=json.dumps(contract_data).encode()) as response:
        result = json.loads(response.read().decode())
        print(f"Success! Created contract ID: {result.get('id')}")
        print(f"Contract: {result.get('contract_name')}")
except urllib.error.HTTPError as e:
    error_body = e.read().decode()
    print(f"Error {e.code}: {error_body}")
except Exception as e:
    print(f"Error: {e}")
