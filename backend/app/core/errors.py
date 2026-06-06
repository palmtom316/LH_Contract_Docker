"""
Unified Error Handling System
Provides standardized error codes and exceptions for the entire application
"""
from enum import Enum
from typing import Optional, Any, Dict
from fastapi import HTTPException, status


class ErrorCode(str, Enum):
    """Standardized error codes for the application"""
    
    # Authentication & Authorization Errors (1xxx)
    INVALID_CREDENTIALS = "1001"
    TOKEN_EXPIRED = "1002"
    TOKEN_INVALID = "1003"
    INSUFFICIENT_PERMISSIONS = "1004"
    USER_NOT_FOUND = "1005"
    USER_INACTIVE = "1006"
    PASSWORD_TOO_WEAK = "1007"
    
    # Contract Business Errors (2xxx)
    CONTRACT_NOT_FOUND = "2001"
    CONTRACT_DUPLICATE = "2002"
    CONTRACT_INVALID_STATUS = "2003"
    CONTRACT_NUMBER_EXISTS = "2004"
    SERIAL_NUMBER_EXISTS = "2005"
    
    # Financial Record Errors (3xxx)
    RECEIVABLE_NOT_FOUND = "3001"
    INVOICE_NOT_FOUND = "3002"
    RECEIPT_NOT_FOUND = "3003"
    SETTLEMENT_NOT_FOUND = "3004"
    AMOUNT_EXCEEDS_LIMIT = "3005"
    INVALID_DATE_RANGE = "3006"
    
    # File Upload Errors (4xxx)
    FILE_TOO_LARGE = "4001"
    FILE_TYPE_NOT_ALLOWED = "4002"
    FILE_UPLOAD_FAILED = "4003"
    FILE_NOT_FOUND = "4004"
    FILE_CORRUPTED = "4005"
    
    # Database Errors (5xxx)
    DATABASE_ERROR = "5001"
    DATABASE_CONNECTION_FAILED = "5002"
    RECORD_NOT_FOUND = "5003"
    DUPLICATE_RECORD = "5004"
    CONSTRAINT_VIOLATION = "5005"
    
    # Validation Errors (6xxx)
    VALIDATION_ERROR = "6001"
    MISSING_REQUIRED_FIELD = "6002"
    INVALID_FORMAT = "6003"
    INVALID_VALUE = "6004"
    
    # System Errors (9xxx)
    INTERNAL_SERVER_ERROR = "9001"
    SERVICE_UNAVAILABLE = "9002"
    RATE_LIMIT_EXCEEDED = "9003"
    CACHE_ERROR = "9004"


class AppException(HTTPException):
    """
    Standardized application exception
    
    Usage:
        raise AppException(
            error_code=ErrorCode.CONTRACT_NOT_FOUND,
            message="合同不存在",
            detail="未找到ID为123的合同",
            status_code=404
        )
    """
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        detail: Optional[str] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        data: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.detail_message = detail
        self.data = data or {}

        response_body = self.to_response()

        super().__init__(
            status_code=status_code,
            detail=response_body
        )

    def to_response(self) -> Dict[str, Any]:
        """Return the canonical API error payload."""
        response_body = {
            "error_code": self.error_code.value,
            "message": self.message,
        }

        if self.detail_message:
            response_body["detail"] = self.detail_message

        if self.data:
            response_body["data"] = self.data

        return response_body


# Predefined exceptions for common scenarios
class AuthenticationError(AppException):
    """Authentication failed"""
    def __init__(self, message: str = "认证失败", detail: Optional[str] = None):
        super().__init__(
            error_code=ErrorCode.INVALID_CREDENTIALS,
            message=message,
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class PermissionDeniedError(AppException):
    """Insufficient permissions"""
    def __init__(self, message: str = "权限不足", detail: Optional[str] = None):
        super().__init__(
            error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            message=message,
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN
        )


class ResourceNotFoundError(AppException):
    """Resource not found"""
    def __init__(
        self,
        resource_type: str = "资源",
        resource_id: Optional[Any] = None,
        error_code: ErrorCode = ErrorCode.RECORD_NOT_FOUND
    ):
        message = f"{resource_type}不存在"
        detail = f"未找到{resource_type}" + (f"，ID: {resource_id}" if resource_id else "")
        
        super().__init__(
            error_code=error_code,
            message=message,
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND
        )


class DuplicateRecordError(AppException):
    """Duplicate record"""
    def __init__(
        self,
        resource_type: str = "记录",
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None
    ):
        message = f"{resource_type}已存在"
        detail = f"{resource_type}重复"
        
        if field_name and field_value:
            detail = f"{field_name} '{field_value}' 已被使用"
        
        super().__init__(
            error_code=ErrorCode.DUPLICATE_RECORD,
            message=message,
            detail=detail,
            status_code=status.HTTP_409_CONFLICT
        )


class ValidationError(AppException):
    """Validation failed"""
    def __init__(
        self,
        message: str = "数据验证失败",
        field_errors: Optional[Dict[str, str]] = None
    ):
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            detail="请检查输入数据",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            data={"field_errors": field_errors} if field_errors else None
        )


class FileUploadError(AppException):
    """File upload failed"""
    def __init__(
        self,
        message: str = "文件上传失败",
        detail: Optional[str] = None,
        error_code: ErrorCode = ErrorCode.FILE_UPLOAD_FAILED
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class DatabaseError(AppException):
    """Database operation failed"""
    def __init__(
        self,
        message: str = "数据库操作失败",
        detail: Optional[str] = None
    ):
        super().__init__(
            error_code=ErrorCode.DATABASE_ERROR,
            message=message,
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
