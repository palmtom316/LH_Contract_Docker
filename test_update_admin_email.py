import urllib.request
import urllib.parse
import json

# Login as admin
login_data = urllib.parse.urlencode({"username": "admin", "password": "admin123"}).encode()
req = urllib.request.Request("http://localhost:8000/api/v1/auth/login", data=login_data, method="POST")
req.add_header("Content-Type", "application/x-www-form-urlencoded")

with urllib.request.urlopen(req) as response:
    token = json.loads(response.read().decode())["access_token"]

# Update admin user email to null
req = urllib.request.Request("http://localhost:8000/api/v1/users/1", method="PUT")
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Content-Type", "application/json")

data = json.dumps({
    "email": None,  # Try to set email to null
    "full_name": "Admin User"
}).encode()

try:
    with urllib.request.urlopen(req, data=data) as response:
        result = json.loads(response.read().decode())
        print(f"Success! User email is now: {result.get('email')}")
except urllib.error.HTTPError as e:
    error_body = e.read().decode()
    print(f"Error {e.code}: {error_body}")
except Exception as e:
    print(f"Error: {e}")
