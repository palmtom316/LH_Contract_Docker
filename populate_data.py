import urllib.request
import json
import random
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

# Enums
CATEGORIES = ["总包合同", "专业分包", "劳务分包", "技术服务", "运营维护", "其他合同"]
COMPANY_CATEGORIES = ["市区配网", "市北配网", "用户工程", "维护工程", "变电工程", "营销工程", "北源工程", "安驰工程"]
PRICING_MODES = ["总价包干", "单价包干", "工日单价", "费率下浮"]
MANAGEMENT_MODES = ["自营", "合作", "挂靠"]
STATUSES = ["进行中", "已完成", "待审核", "已终止"]

def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    
    if data:
        data_bytes = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    else:
        data_bytes = None
        
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            if response.status >= 200 and response.status < 300:
                result = response.read().decode('utf-8')
                return json.loads(result) if result else {}
            else:
                print(f"Error: {response.status}")
                return None
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"Request Error: {e}")
        return None

def get_token():
    url = f"{BASE_URL}/auth/login/json"
    payload = {
        "username": USERNAME,
        "password": PASSWORD
    }
    resp = make_request(url, "POST", payload)
    if resp:
        return resp.get("access_token")
    return None

def generate_contract(index):
    now = datetime.now()
    sign_date = now - timedelta(days=random.randint(1, 365))
    code = f"LH-{sign_date.strftime('%Y%m')}-{index+1:03d}"
    amount = round(random.uniform(50000, 5000000), 2)
    
    return {
        "contract_code": code,
        "contract_name": f"示例合同项目-{index+1}期工程",
        "party_a_name": f"上海电力公司{random.choice(['市北', '市区', '浦东'])}供电分公司",
        "party_b_name": "上海蓝海电气有限公司",
        "contract_amount": amount,
        "sign_date": sign_date.strftime('%Y-%m-%d'),
        "category": random.choice(CATEGORIES),
        "company_category": random.choice(COMPANY_CATEGORIES),
        "pricing_mode": random.choice(PRICING_MODES),
        "management_mode": random.choice(MANAGEMENT_MODES),
        "responsible_person": random.choice(["张伟", "李强", "王芳", "赵敏"]),
        "start_date": (sign_date + timedelta(days=10)).strftime('%Y-%m-%d'),
        "end_date": (sign_date + timedelta(days=365)).strftime('%Y-%m-%d'),
        "status": random.choice(STATUSES),
        "notes": f"这是第 {index+1} 条自动生成的测试数据"
    }

def main():
    print("Getting token...")
    token = get_token()
    if not token:
        print("Failed to get token")
        return

    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print("Creating contracts...")
    for i in range(10):
        data = generate_contract(i)
        url = f"{BASE_URL}/contracts/upstream/"
        print(f"Creating: {data['contract_name']}...")
        resp = make_request(url, "POST", data, headers)
        if resp:
            print(f"[{i+1}/10] Success")
        else:
            print(f"[{i+1}/10] Failed")

if __name__ == "__main__":
    main()
