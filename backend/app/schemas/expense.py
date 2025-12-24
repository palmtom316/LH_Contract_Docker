"""
Expense Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from app.models.enums import ExpenseCategory, ExpenseType


class ExpenseBase(BaseModel):
    """Base expense schema"""
    expense_code: str = Field(..., max_length=50)
    attribution: Optional[str] = None
    category: str
    expense_type: Optional[str] = None
    amount: Decimal = Field(..., ge=0)
    expense_date: date
    
    handler: Optional[str] = Field(None, max_length=100)
    responsible_person: Optional[str] = Field(None, max_length=100)
    upstream_contract_id: Optional[int] = None
    
    description: Optional[str] = None
    file_path: Optional[str] = None
    status: Optional[str] = Field(default="待审核", max_length=50)


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    expense_code: Optional[str] = Field(None, max_length=50)  # 允许更新费用编号
    attribution: Optional[str] = None
    category: Optional[str] = None
    expense_type: Optional[str] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    expense_date: Optional[date] = None
    
    handler: Optional[str] = Field(None, max_length=100)
    responsible_person: Optional[str] = Field(None, max_length=100)
    upstream_contract_id: Optional[int] = None
    
    description: Optional[str] = None
    file_path: Optional[str] = None
    status: Optional[str] = Field(None, max_length=50)


class ExpenseRef(BaseModel):
    pass

class UpstreamContractRef(BaseModel):
    id: int
    contract_name: str
    contract_code: str
    class Config:
        from_attributes = True

class ExpenseResponse(ExpenseBase):
    id: int
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    upstream_contract: Optional[UpstreamContractRef] = None

    class Config:
        from_attributes = True


class ExpenseListResponse(BaseModel):
    items: List[ExpenseResponse]
    total: int
    page: int
    page_size: int


class ExpenseSummary(BaseModel):
    category: str
    total_amount: Decimal
    count: int
