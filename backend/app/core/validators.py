"""
Enhanced Pydantic Validators
Provides reusable validators for common data validation scenarios.

Features:
- Money/Amount validation
- Date range validation
- Contract code format validation
- Chinese text validation
- File path validation
"""
from typing import Optional, Any, List
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
import re
from pydantic import field_validator, model_validator, ValidationInfo
from functools import wraps


class MoneyValidators:
    """Validators for monetary amounts"""
    
    @staticmethod
    def validate_amount(value: Any, field_name: str = "amount") -> Decimal:
        """
        Validate and convert a monetary amount.
        
        Args:
            value: The value to validate
            field_name: Field name for error messages
            
        Returns:
            Decimal value
            
        Raises:
            ValueError: If value is invalid
        """
        if value is None:
            return Decimal("0")
        
        try:
            if isinstance(value, str):
                # Remove common formatting
                value = value.replace(",", "").replace("¥", "").replace("￥", "").strip()
            
            decimal_value = Decimal(str(value))
            
            # Check for negative values
            if decimal_value < 0:
                raise ValueError(f"{field_name} 不能为负数")
            
            # Round to 2 decimal places
            return decimal_value.quantize(Decimal("0.01"))
            
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"{field_name} 无效的金额格式: {value}")
    
    @staticmethod
    def validate_non_negative(value: Any) -> Decimal:
        """Validate that amount is non-negative"""
        if value is None:
            return Decimal("0")
        
        decimal_value = Decimal(str(value))
        if decimal_value < 0:
            raise ValueError("金额不能为负数")
        
        return decimal_value.quantize(Decimal("0.01"))
    
    @staticmethod
    def validate_positive(value: Any) -> Decimal:
        """Validate that amount is positive"""
        if value is None:
            raise ValueError("金额不能为空")
        
        decimal_value = Decimal(str(value))
        if decimal_value <= 0:
            raise ValueError("金额必须大于零")
        
        return decimal_value.quantize(Decimal("0.01"))


class DateValidators:
    """Validators for date fields"""
    
    @staticmethod
    def validate_date_not_future(value: date, field_name: str = "日期") -> date:
        """Validate that date is not in the future"""
        if value and value > date.today():
            raise ValueError(f"{field_name} 不能是未来日期")
        return value
    
    @staticmethod
    def validate_date_not_past(value: date, field_name: str = "日期") -> date:
        """Validate that date is not in the past"""
        if value and value < date.today():
            raise ValueError(f"{field_name} 不能是过去日期")
        return value
    
    @staticmethod
    def validate_date_range(
        start_date: Optional[date],
        end_date: Optional[date],
        allow_same: bool = True
    ) -> tuple:
        """
        Validate that end_date is after start_date.
        
        Returns:
            tuple of (start_date, end_date)
        """
        if start_date and end_date:
            if allow_same:
                if end_date < start_date:
                    raise ValueError("结束日期不能早于开始日期")
            else:
                if end_date <= start_date:
                    raise ValueError("结束日期必须晚于开始日期")
        
        return (start_date, end_date)
    
    @staticmethod
    def validate_year(value: int) -> int:
        """Validate year is reasonable"""
        current_year = date.today().year
        if value < 2000 or value > current_year + 10:
            raise ValueError(f"年份必须在 2000 到 {current_year + 10} 之间")
        return value


class StringValidators:
    """Validators for string fields"""
    
    @staticmethod
    def validate_not_empty(value: Optional[str], field_name: str = "字段") -> str:
        """Validate that string is not empty or whitespace"""
        if not value or not value.strip():
            raise ValueError(f"{field_name} 不能为空")
        return value.strip()
    
    @staticmethod
    def validate_max_length(value: str, max_length: int, field_name: str = "字段") -> str:
        """Validate string does not exceed max length"""
        if value and len(value) > max_length:
            raise ValueError(f"{field_name} 不能超过 {max_length} 个字符")
        return value
    
    @staticmethod
    def validate_contract_code(value: Optional[str]) -> Optional[str]:
        """
        Validate contract code format.
        Allows alphanumeric, Chinese characters, and common separators.
        """
        if not value:
            return value
        
        value = value.strip()
        
        # Allow: letters, numbers, Chinese, hyphen, underscore, slash
        pattern = r'^[\w\u4e00-\u9fa5\-_/]+$'
        if not re.match(pattern, value):
            raise ValueError("合同编号只能包含字母、数字、中文、连字符、下划线和斜杠")
        
        if len(value) > 50:
            raise ValueError("合同编号不能超过 50 个字符")
        
        return value
    
    @staticmethod
    def validate_phone(value: Optional[str]) -> Optional[str]:
        """Validate Chinese mobile phone number"""
        if not value:
            return value
        
        value = value.strip().replace("-", "").replace(" ", "")
        
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise ValueError("请输入有效的手机号码")
        
        return value
    
    @staticmethod
    def validate_email(value: Optional[str]) -> Optional[str]:
        """Validate email format"""
        if not value:
            return value
        
        value = value.strip().lower()
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, value):
            raise ValueError("请输入有效的邮箱地址")
        
        return value
    
    @staticmethod
    def sanitize_html(value: str) -> str:
        """Remove HTML tags from string"""
        if not value:
            return value
        
        return re.sub(r'<[^>]+>', '', value)


class ContractValidators:
    """Validators specific to contract data"""
    
    @staticmethod
    def validate_pricing_mode(value: str) -> str:
        """Validate pricing mode"""
        valid_modes = ["固定总价", "单价合同", "成本加成", "其他"]
        if value and value not in valid_modes:
            raise ValueError(f"计价模式必须是以下之一: {', '.join(valid_modes)}")
        return value
    
    @staticmethod
    def validate_status(value: str) -> str:
        """Validate contract status"""
        valid_statuses = ["进行中", "已完成", "已结算", "已取消", "未开始", "待收款", "待付款"]
        if value and value not in valid_statuses:
            raise ValueError(f"状态必须是以下之一: {', '.join(valid_statuses)}")
        return value
    
    @staticmethod
    def validate_settlement_not_exceed_contract(
        settlement_amount: Decimal,
        contract_amount: Decimal,
        tolerance_percent: float = 20.0
    ) -> None:
        """
        Validate settlement amount is within reasonable range of contract amount.
        
        Args:
            settlement_amount: Settlement amount
            contract_amount: Original contract amount
            tolerance_percent: Allowed variance percentage
        """
        if contract_amount > 0:
            max_allowed = contract_amount * Decimal(str(1 + tolerance_percent / 100))
            if settlement_amount > max_allowed:
                raise ValueError(
                    f"结算金额 ({settlement_amount}) 超过合同金额 ({contract_amount}) 的 {tolerance_percent}%"
                )


class FileValidators:
    """Validators for file-related fields"""
    
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'xlsx', 'xls', 'doc', 'docx'}
    ALLOWED_PDF_ONLY = {'pdf'}
    ALLOWED_IMAGES = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    
    @staticmethod
    def validate_file_extension(
        filename: Optional[str],
        allowed: set = None
    ) -> Optional[str]:
        """Validate file has allowed extension"""
        if not filename:
            return filename
        
        allowed = allowed or FileValidators.ALLOWED_EXTENSIONS
        
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in allowed:
            raise ValueError(f"不支持的文件类型。允许的类型: {', '.join(allowed)}")
        
        return filename
    
    @staticmethod
    def validate_file_path(value: Optional[str]) -> Optional[str]:
        """Validate file path is safe (no path traversal)"""
        if not value:
            return value
        
        # Check for path traversal attempts
        if '..' in value or value.startswith('/') or '\\' in value:
            raise ValueError("非法的文件路径")
        
        return value


# Decorator for creating field validators
def amount_validator(field_name: str):
    """
    Decorator to create a Pydantic field validator for amounts.
    
    Usage:
        @amount_validator("contract_amount")
        def validate_contract_amount(cls, v):
            return v
    """
    def decorator(func):
        @wraps(func)
        def wrapper(cls, v):
            if v is not None:
                v = MoneyValidators.validate_amount(v, field_name)
            return func(cls, v)
        return wrapper
    return decorator


# Common validation patterns as re-usable validators
def create_amount_validator():
    """Create a field validator for monetary amounts"""
    @field_validator('amount', 'contract_amount', 'settlement_amount', 
                     'total_amount', 'payable_amount', 'paid_amount',
                     mode='before', check_fields=False)
    @classmethod
    def validate_amounts(cls, v: Any) -> Decimal:
        return MoneyValidators.validate_non_negative(v)
    return validate_amounts


def create_date_validator():
    """Create a field validator for dates"""
    @field_validator('sign_date', 'expected_date', 'payment_date', 
                     'receipt_date', 'settlement_date',
                     mode='before', check_fields=False)
    @classmethod
    def validate_dates(cls, v: Any) -> Optional[date]:
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError("日期格式无效，请使用 YYYY-MM-DD 格式")
        return v
    return validate_dates
