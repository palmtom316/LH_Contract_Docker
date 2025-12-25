"""
Contract Code Generator Service

Generates contract codes with format: PREFIX-YYYY-MM-NNN
- S: 上游合同 (Upstream) - 使用签约日期
- X: 下游合同 (Downstream) - 使用签约日期
- G: 管理合同 (Management) - 使用签约日期
- F: 无合同费用 (Expense) - 使用费用发生日期

Each month the sequence number resets to 001.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from datetime import datetime, date
from typing import Literal, Optional, Union

from app.models.contract_upstream import ContractUpstream
from app.models.contract_downstream import ContractDownstream
from app.models.contract_management import ContractManagement
from app.models.expense import ExpenseNonContract


class ContractCodeGenerator:
    """Contract code generator service"""
    
    PREFIX_MAP = {
        'upstream': 'S',    # 上游合同
        'downstream': 'X',  # 下游合同
        'management': 'G',  # 管理合同
        'expense': 'F',     # 无合同费用
    }
    
    MODEL_MAP = {
        'upstream': ContractUpstream,
        'downstream': ContractDownstream,
        'management': ContractManagement,
        'expense': ExpenseNonContract,
    }
    
    CODE_FIELD_MAP = {
        'upstream': 'contract_code',
        'downstream': 'contract_code',
        'management': 'contract_code',
        'expense': 'expense_code',
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_code(
        self, 
        contract_type: Literal['upstream', 'downstream', 'management', 'expense'],
        reference_date: Optional[Union[date, datetime, str]] = None
    ) -> str:
        """
        Generate a new contract code for the given type.
        
        Format: PREFIX-YYYY-MM-NNN
        Example: S-2025-12-001, X-2025-12-002, G-2025-12-001, F-2025-12-001
        
        Args:
            contract_type: One of 'upstream', 'downstream', 'management', 'expense'
            reference_date: The date to use for year/month (sign_date or expense_date).
                           If None, uses current date.
            
        Returns:
            Generated contract code string
        """
        prefix = self.PREFIX_MAP[contract_type]
        model = self.MODEL_MAP[contract_type]
        code_field = self.CODE_FIELD_MAP[contract_type]
        
        # Parse the reference date
        if reference_date is None:
            ref_date = datetime.now()
        elif isinstance(reference_date, str):
            try:
                ref_date = datetime.strptime(reference_date, '%Y-%m-%d')
            except ValueError:
                ref_date = datetime.now()
        elif isinstance(reference_date, date) and not isinstance(reference_date, datetime):
            ref_date = datetime.combine(reference_date, datetime.min.time())
        else:
            ref_date = reference_date
        
        year = ref_date.year
        month = ref_date.month
        
        # Format: S-2025-12-
        code_prefix = f"{prefix}-{year}-{month:02d}-"
        
        # Find the max sequence number for this month
        # Look for codes matching the pattern
        code_column = getattr(model, code_field)
        query = select(func.max(code_column)).where(
            code_column.like(f"{code_prefix}%")
        )
        result = await self.db.execute(query)
        max_code = result.scalar_one_or_none()
        
        if max_code:
            # Extract the sequence number from the last code
            try:
                # Get the last part after the prefix (e.g., "001" from "S-2025-12-001")
                seq_str = max_code.replace(code_prefix, "")
                current_seq = int(seq_str)
                next_seq = current_seq + 1
            except (ValueError, AttributeError):
                # If parsing fails, start from 1
                next_seq = 1
        else:
            next_seq = 1
        
        # Generate the new code with 3-digit sequence
        new_code = f"{code_prefix}{next_seq:03d}"
        
        return new_code
    
    async def generate_upstream_code(self, sign_date: Optional[Union[date, datetime, str]] = None) -> str:
        """Generate code for upstream contract (S-YYYY-MM-NNN) based on sign_date"""
        return await self.generate_code('upstream', sign_date)
    
    async def generate_downstream_code(self, sign_date: Optional[Union[date, datetime, str]] = None) -> str:
        """Generate code for downstream contract (X-YYYY-MM-NNN) based on sign_date"""
        return await self.generate_code('downstream', sign_date)
    
    async def generate_management_code(self, sign_date: Optional[Union[date, datetime, str]] = None) -> str:
        """Generate code for management contract (G-YYYY-MM-NNN) based on sign_date"""
        return await self.generate_code('management', sign_date)
    
    async def generate_expense_code(self, expense_date: Optional[Union[date, datetime, str]] = None) -> str:
        """Generate code for non-contract expense (F-YYYY-MM-NNN) based on expense_date"""
        return await self.generate_code('expense', expense_date)


async def get_next_contract_code(
    db: AsyncSession, 
    contract_type: Literal['upstream', 'downstream', 'management', 'expense'],
    reference_date: Optional[Union[date, datetime, str]] = None
) -> str:
    """
    Convenience function to get the next contract code.
    
    Args:
        db: Database session
        contract_type: One of 'upstream', 'downstream', 'management', 'expense'
        reference_date: The date to use for year/month
        
    Returns:
        Generated contract code
    """
    generator = ContractCodeGenerator(db)
    return await generator.generate_code(contract_type, reference_date)
