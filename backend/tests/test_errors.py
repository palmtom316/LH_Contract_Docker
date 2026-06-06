"""
Error handling contract tests.
"""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.errors import (
    AppException,
    AuthenticationError,
    DuplicateRecordError,
    ErrorCode,
    ResourceNotFoundError,
    ValidationError,
)
from app.main import app_exception_handler


@pytest.fixture
def error_test_app():
    app = FastAPI()
    app.add_exception_handler(AppException, app_exception_handler)

    @app.get("/app-exception")
    async def raise_app_exception():
        raise AppException(
            error_code=ErrorCode.CONTRACT_NOT_FOUND,
            message="合同不存在",
            detail="未找到指定合同",
            status_code=404,
        )

    @app.get("/validation-exception")
    async def raise_validation_error():
        raise ValidationError(
            message="数据验证失败",
            field_errors={"contract_code": "合同编号不能为空"},
        )

    return app


@pytest.mark.asyncio
class TestErrorResponseContract:
    async def test_app_exception_handler_returns_structured_payload(self, error_test_app: FastAPI):
        transport = ASGITransport(app=error_test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/app-exception")

        assert response.status_code == 404
        assert response.json() == {
            "error_code": ErrorCode.CONTRACT_NOT_FOUND.value,
            "message": "合同不存在",
            "detail": "未找到指定合同",
        }

    async def test_validation_error_handler_includes_field_errors(self, error_test_app: FastAPI):
        transport = ASGITransport(app=error_test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/validation-exception")

        assert response.status_code == 422
        assert response.json() == {
            "error_code": ErrorCode.VALIDATION_ERROR.value,
            "message": "数据验证失败",
            "detail": "请检查输入数据",
            "data": {
                "field_errors": {
                    "contract_code": "合同编号不能为空",
                }
            },
        }


class TestCustomExceptions:
    def test_app_exception_exposes_structured_response_body(self):
        exc = AppException(
            error_code=ErrorCode.CONTRACT_NOT_FOUND,
            message="合同不存在",
            detail="未找到指定合同",
            status_code=404,
        )

        assert exc.status_code == 404
        assert exc.error_code == ErrorCode.CONTRACT_NOT_FOUND
        assert exc.message == "合同不存在"
        assert exc.detail_message == "未找到指定合同"
        assert exc.to_response() == {
            "error_code": ErrorCode.CONTRACT_NOT_FOUND.value,
            "message": "合同不存在",
            "detail": "未找到指定合同",
        }
        assert exc.detail == exc.to_response()

    def test_authentication_error_uses_standard_error_code(self):
        exc = AuthenticationError("登录失败")

        assert exc.status_code == 401
        assert exc.error_code == ErrorCode.INVALID_CREDENTIALS
        assert exc.to_response()["message"] == "登录失败"

    def test_resource_not_found_error_formats_detail_message(self):
        exc = ResourceNotFoundError(
            resource_type="合同",
            resource_id=123,
        )

        assert exc.status_code == 404
        assert exc.message == "合同不存在"
        assert exc.detail_message == "未找到合同，ID: 123"
        assert exc.to_response()["detail"] == "未找到合同，ID: 123"

    def test_duplicate_record_error_formats_detail_message(self):
        exc = DuplicateRecordError(
            resource_type="合同",
            field_name="contract_code",
            field_value="TEST-001",
        )

        assert exc.status_code == 409
        assert exc.detail_message == "contract_code 'TEST-001' 已被使用"
        assert exc.to_response()["detail"] == "contract_code 'TEST-001' 已被使用"

    def test_validation_error_serializes_field_errors(self):
        field_errors = {
            "contract_code": "合同编号不能为空",
            "contract_amount": "金额必须大于0",
        }

        exc = ValidationError(
            message="数据验证失败",
            field_errors=field_errors,
        )

        assert exc.status_code == 422
        assert exc.detail_message == "请检查输入数据"
        assert exc.to_response()["data"] == {"field_errors": field_errors}
