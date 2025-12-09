"""
Expense Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from app.models.expense import ExpenseCategoryType, ExpenseType


class ExpenseBase(BaseModel):
    """Base expense schema"""
    expense_code: str = Field(..., max_length=50)
    category: ExpenseCategoryType
    expense_type: ExpenseType
    amount: Decimal = Field(..., ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    expense_date: date
    payment_date: Optional[date] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    payee_name: Optional[str] = Field(None, max_length=200)
    invoice_number: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = Field(default="待审核", max_length=50)


class ExpenseCreate(ExpenseBase):
    """Schema for creating expense"""
    pass


class ExpenseUpdate(BaseModel):
    """Schema for updating expense"""
    category: Optional[ExpenseCategoryType] = None
    expense_type: Optional[ExpenseType] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    expense_date: Optional[date] = None
    payment_date: Optional[date] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    payee_name: Optional[str] = Field(None, max_length=200)
    invoice_number: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = Field(None, max_length=50)


class ExpenseResponse(ExpenseBase):
    """Schema for expense response"""
    id: int
    invoice_file_path: Optional[str] = None
    receipt_file_path: Optional[str] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


class ExpenseListResponse(BaseModel):
    """Schema for paginated expenses list"""
    items: List[ExpenseResponse]
    total: int
    page: int
    page_size: int


class ExpenseSummary(BaseModel):
    """Schema for expense summary by category"""
    category: ExpenseCategoryType
    total_amount: Decimal
    count: int
