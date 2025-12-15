import urllib.request
import urllib.parse
import json
import sys

# Login
login_data = urllib.parse.urlencode({"username": "admin", "password": "admin123"}).encode()
req = urllib.request.Request("http://localhost:8000/api/v1/auth/login", data=login_data, method="POST")
req.add_header("Content-Type", "application/x-www-form-urlencoded")

with urllib.request.urlopen(req) as response:
    token = json.loads(response.read().decode())["access_token"]
    print(f"✓ Logged in, token: {token[:20]}...")

# Create a new contract (serial_number 13)
contract_data = {
    "serial_number": 13,
    "contract_code": "DEBUG-TEST-001",
    "contract_name": "调试测试合同",
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

print(f"\n发送数据:")
print(json.dumps(contract_data, indent=2, ensure_ascii=False))

req = urllib.request.Request("http://localhost:8000/api/v1/contracts/upstream/", method="POST")
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Content-Type", "application/json")

try:
    with urllib.request.urlopen(req, data=json.dumps(contract_data).encode()) as response:
        result = json.loads(response.read().decode())
        print(f"\n✓ Success! Created contract:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
except urllib.error.HTTPError as e:
    error_body = e.read().decode()
    print(f"\n✗ Error {e.code}:")
    try:
        error_json = json.loads(error_body)
        print(json.dumps(error_json, indent=2, ensure_ascii=False))
    except:
        print(error_body)
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
