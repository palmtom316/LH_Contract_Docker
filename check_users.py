import urllib.request
import urllib.parse
import json

# Login
login_data = urllib.parse.urlencode({"username": "admin", "password": "admin123"}).encode()
req = urllib.request.Request("http://localhost:8000/api/v1/auth/login", data=login_data, method="POST")
req.add_header("Content-Type", "application/x-www-form-urlencoded")

with urllib.request.urlopen(req) as response:
    token = json.loads(response.read().decode())["access_token"]

# Get users
req = urllib.request.Request("http://localhost:8000/api/v1/users/", method="GET")
req.add_header("Authorization", f"Bearer {token}")

try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        # data is a list of users, not a paginated response
        print(f"Total users: {len(data)}")
        print(f"Users:")
        for user in data:
            print(f"  - {user['username']} ({user.get('full_name', 'N/A')}) - {user['role']}")
except Exception as e:
    print(f"Error: {e}")
