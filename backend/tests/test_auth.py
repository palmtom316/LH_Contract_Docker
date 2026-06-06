"""
Authentication Tests
Tests for user authentication, login, and token management
"""
import pytest
from httpx import AsyncClient
from app.models.user import User


@pytest.mark.asyncio
class TestAuthentication:
    """Test authentication endpoints"""
    
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login"""
        response = await client.post(
            "/api/v1/auth/login/json",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testuser"
    
    async def test_login_invalid_credentials(self, client: AsyncClient, test_user: User):
        """Test login with invalid credentials"""
        response = await client.post(
            "/api/v1/auth/login/json",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        payload = response.json()
        assert payload["message"] == "用户名或密码错误"
        assert payload["detail"] == "请检查您的登录凭据"
    
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user"""
        response = await client.post(
            "/api/v1/auth/login/json",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
    
    async def test_get_current_user(self, client: AsyncClient, test_user: User, user_token: str):
        """Test getting current user information"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
    
    async def test_get_current_user_no_token(self, client: AsyncClient):
        """Test accessing protected route without token"""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test accessing protected route with invalid token"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401

    async def test_refresh_token_cannot_call_me_endpoint(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Refresh tokens must not authenticate protected business routes"""
        login_response = await client.post(
            "/api/v1/auth/login/json",
            json={
                "username": "testuser",
                "password": "testpass123",
            },
        )
        assert login_response.status_code == 200

        refresh_token = login_response.json()["refresh_token"]
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )

        assert response.status_code == 401


@pytest.mark.asyncio
class TestPasswordValidation:
    """Test password strength validation"""
    
    async def test_weak_password_too_short(self, client: AsyncClient):
        """Test registration with too short password"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "short",  # Too short
                "full_name": "New User",
                "role": "BIDDING"
            }
        )
        
        # Should be rejected (password too short)
        assert response.status_code in [400, 422]
    
    async def test_weak_password_no_number(self, client: AsyncClient):
        """Test registration with password missing numbers"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "onlyletters",  # No numbers
                "full_name": "New User",
                "role": "BIDDING"
            }
        )

        assert response.status_code == 403
        assert response.json()["message"] == "公开注册已关闭"
    
    async def test_valid_password(self, client: AsyncClient):
        """Public registration should be closed even with a valid password"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "ValidPass123",  # Valid
                "full_name": "New User",
                "role": "BIDDING"
            }
        )

        assert response.status_code == 403
        assert response.json()["message"] == "公开注册已关闭"


@pytest.mark.asyncio
class TestPermissions:
    """Test role-based permissions"""
    
    async def test_admin_can_access_admin_route(
        self, 
        client: AsyncClient, 
        test_admin: User,
        admin_token: str
    ):
        """Test admin accessing admin-only route"""
        response = await client.get(
            "/api/v1/auth/roles",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert "roles" in response.json()
    
    async def test_user_cannot_access_admin_route(
        self,
        client: AsyncClient,
        test_user: User,
        user_token: str
    ):
        """Test regular user accessing admin-only route"""
        response = await client.get(
            "/api/v1/auth/roles",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        # Should be forbidden
        assert response.status_code == 403
