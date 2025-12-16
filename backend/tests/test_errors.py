"""
Error Handling Tests
Tests for unified error handling system
"""
import pytest
from httpx import AsyncClient

from app.core.errors import (
    AppException,
    ErrorCode,
    AuthenticationError,
    ResourceNotFoundError,
    DuplicateRecordError,
    ValidationError
)


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and responses"""
    
    async def test_404_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test 404 error for nonexistent resource"""
        response = await client.get(
            "/api/v1/contracts/upstream/999999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    async def test_validation_error(self, client: AsyncClient, auth_headers: dict):
        """Test validation error with invalid data"""
        response = await client.post(
            "/api/v1/contracts/upstream/",
            headers=auth_headers,
            json={
                # Missing required fields
                "contract_code": "TEST-001"
                # Missing contract_name, party_a, contract_amount, etc.
            }
        )
        
        # Should return 422 Unprocessable Entity
        assert response.status_code == 422
    
    async def test_duplicate_error(self, client: AsyncClient, auth_headers: dict):
        """Test duplicate record error"""
        # Create first contract
        contract_data = {
            "contract_code": "DUPLICATE-TEST",
            "contract_name": "Test Contract",
            "party_a_name": "Party A",
            "party_b_name": "Party B",
            "contract_amount": 100000,
            "sign_date": "2024-01-01"
        }
        
        response1 = await client.post(
            "/api/v1/contracts/upstream/",
            headers=auth_headers,
            json=contract_data
        )
        
        # Try to create duplicate
        response2 = await client.post(
            "/api/v1/contracts/upstream/",
            headers=auth_headers,
            json=contract_data
        )
        
        # Second should fail with duplicate error
        assert response2.status_code in [400, 409]  # Conflict or Bad Request


@pytest.mark.asyncio
class TestCustomExceptions:
    """Test custom exception classes"""
    
    def test_app_exception_structure(self):
        """Test AppException creates proper structure"""
        exc = AppException(
            error_code=ErrorCode.CONTRACT_NOT_FOUND,
            message="合同不存在",
            detail="未找到指定合同",
            status_code=404
        )
        
        assert exc.status_code == 404
        assert exc.error_code == ErrorCode.CONTRACT_NOT_FOUND
        assert exc.message == "合同不存在"
        assert exc.detail == "未找到指定合同"
    
    def test_authentication_error(self):
        """Test AuthenticationError"""
        exc = AuthenticationError("登录失败")
        
        assert exc.status_code == 401
        assert exc.error_code == ErrorCode.INVALID_CREDENTIALS
    
    def test_resource_not_found_error(self):
        """Test ResourceNotFoundError"""
        exc = ResourceNotFoundError(
            resource_type="合同",
            resource_id=123
        )
        
        assert exc.status_code == 404
        assert "合同" in exc.message
        assert "123" in exc.detail
    
    def test_duplicate_record_error(self):
        """Test DuplicateRecordError"""
        exc = DuplicateRecordError(
            resource_type="合同",
            field_name="contract_code",
            field_value="TEST-001"
        )
        
        assert exc.status_code == 409
        assert "TEST-001" in exc.detail
    
    def test_validation_error(self):
        """Test ValidationError with field errors"""
        field_errors = {
            "contract_code": "合同编号不能为空",
            "contract_amount": "金额必须大于0"
        }
        
        exc = ValidationError(
            message="数据验证失败",
            field_errors=field_errors
        )
        
        assert exc.status_code == 422
        assert exc.data["field_errors"] == field_errors
