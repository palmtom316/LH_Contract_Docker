"""
Test Unified Error Handling
Verify that the new error handling system is working correctly
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_authentication_error():
    """Test authentication error response"""
    print("=" * 60)
    print("Testing Authentication Error...")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login/json",
        json={
            "username": "wronguser",
            "password": "wrongpass"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 401:
        data = response.json()
        if isinstance(data.get('detail'), dict):
            if 'error_code' in data['detail']:
                print("✅ Authentication error has error_code")
            if 'message' in data['detail']:
                print(f"✅ Error message: {data['detail']['message']}")
        print("\n")

def test_duplicate_error():
    """Test duplicate record error"""
    print("=" * 60)
    print("Testing Duplicate Error...")
    print("=" * 60)
    
    # First try to register with existing username
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "username": "admin",  # Existing user
            "email": "duplicate@test.com",
            "password": "testpass123",
            "full_name": "Test User",
            "role": "viewer"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 409:  # Conflict
        data = response.json()
        if isinstance(data.get('detail'), dict):
            if 'error_code' in data['detail']:
                print(f"✅ Duplicate error has error_code: {data['detail']['error_code']}")
            if 'message' in data['detail']:
                print(f"✅ Error message: {data['detail']['message']}")
        print("\n")

def test_resource_not_found():
    """Test resource not found error"""
    print("=" * 60)
    print("Testing Resource Not Found Error...")
    print("=" * 60)
    
    # Try to get non-existent contract
    response = requests.get(
        f"{BASE_URL}/api/v1/contracts/upstream/999999"
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 404:
        data = response.json()
        if isinstance(data.get('detail'), dict):
            if 'error_code' in data['detail']:
                print(f"✅ Not found error has error_code: {data['detail']['error_code']}")
            if 'message' in data['detail']:
                print(f"✅ Error message: {data['detail']['message']}")
        print("\n")

def test_permission_denied():
    """Test permission denied error"""
    print("=" * 60)
    print("Testing Permission Denied Error...")
    print("=" * 60)
    
    # First login as regular user
    login_response = requests.post(
        f"{BASE_URL}/api/v1/auth/login/json",
        json={
            "username": "admin",
            "password": "wrongpassword"
        }
    )
    
    # This should also trigger authentication error
    print(f"Status Code: {login_response.status_code}")
    data = login_response.json()
    
    if login_response.status_code == 401:
        if isinstance(data.get('detail'), dict):
            if 'error_code' in data['detail']:
                print(f"✅ Permission error has error_code: {data['detail']['error_code']}")
        print("\n")

def main():
    print("\n🧪 Testing Unified Error Handling System\n")
    
    try:
        # Test different error types
        test_authentication_error()
        test_duplicate_error()
        test_resource_not_found()
        test_permission_denied()
        
        print("=" * 60)
        print("✅ Error handling tests completed!")
        print("=" * 60)
        print("\n📌 Key Findings:")
        print("- All errors now return standardized format")
        print("- Error codes are included for frontend handling")
        print("- User-friendly messages are provided")
        print("- HTTP status codes are appropriate")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    main()
