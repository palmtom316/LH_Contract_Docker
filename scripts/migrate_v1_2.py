
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))

from sqlalchemy import text, inspect
from app.database import engine, Base
from app.models.system import SysDictionary, SystemConfig
from app.models.enums import (
    ContractCategory, PricingMode, ManagementMode, 
    PaymentCategory, ReceivableCategory, 
    DownstreamContractCategory, ExpenseCategory, ExpenseType
)
from sqlalchemy.ext.asyncio import AsyncSession

async def migrate_v1_2():
    print("Starting Migration for V1.2...")
    
    async with engine.begin() as conn:
        # 1. Create new tables
        print("Creating new system tables...")
        await conn.run_sync(Base.metadata.create_all)
        
        # 2. Populate SysDictionary with initial values from Enums
        print("Populating SysDictionary...")
        
        # Helper to insert if not exists
        # We'll do this in a session
        
    async with AsyncSession(engine) as session:
        # Define mappings
        mappings = [
            ("contract_category", ContractCategory),
            ("pricing_mode", PricingMode),
            ("management_mode", ManagementMode),
            ("payment_category", PaymentCategory),
            ("receivable_category", ReceivableCategory),
            ("downstream_contract_category", DownstreamContractCategory),
            ("expense_category", ExpenseCategory),
            ("expense_type", ExpenseType),
            # Add other mappings if needed
        ]
        
        count = 0
        for category_name, enum_cls in mappings:
            for i, member in enumerate(enum_cls):
                exists = await session.execute(
                    text("SELECT 1 FROM sys_dictionaries WHERE category = :cat AND value = :val"),
                    {"cat": category_name, "val": member.value}
                )
                if not exists.scalar():
                    new_item = SysDictionary(
                        category=category_name,
                        label=member.value, # Use the string value (e.g., "总包合同") as both label and value
                        value=member.value,
                        sort_order=i,
                        is_active=True
                    )
                    session.add(new_item)
                    count += 1
        
        # Add default system config
        default_configs = [
            ("system_name", "合同管理系统"),
            ("system_logo", "")
        ]
        
        for key, val in default_configs:
            exists = await session.execute(
                text("SELECT 1 FROM sys_config WHERE key = :key"),
                {"key": key}
            )
            if not exists.scalar():
                session.add(SystemConfig(key=key, value=val))
                count += 1
                
        await session.commit()
        print(f"Added {count} dictionary/config items.")

    # 3. Alter Column Types (Migrate Enums to String)
    # This involves raw SQL to alter columns and drop types
    async with engine.begin() as conn:
        print("Converting Enum columns to String...")
        
        # List of (Table, Column, EnumType)
        conversions = [
            # Upstream
            ("contracts_upstream", "category", "contractcategory"),
            ("contracts_upstream", "pricing_mode", "pricingmode"),
            ("contracts_upstream", "management_mode", "managementmode"),
            ("finance_upstream_receivables", "category", "receivablecategory"),
            
            # Downstream
            ("contracts_downstream", "pricing_mode", "pricingmode"),
            ("contracts_downstream", "management_mode", "managementmode"),
            ("finance_downstream_payables", "category", "paymentcategory"),
            
            # Management
            ("contracts_management", "pricing_mode", "pricingmode"),
            ("contracts_management", "management_mode", "managementmode"),
            ("finance_management_payables", "category", "paymentcategory"),
        ]
        
        for table, col, type_name in conversions:
            try:
                # Check if column uses enum (this is heuristic, we just try to alter it)
                # Alter column to text
                await conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE VARCHAR(255) USING {col}::text"))
                print(f"Altered {table}.{col} to VARCHAR.")
            except Exception as e:
                print(f"Skipping {table}.{col} (might already be string): {e}")
        
        # Drop Enum Types
        # Note: multiple columns might share an enum type, so we drop if exists only after all alters
        enum_types = [
            "contractcategory", "pricingmode", "managementmode", 
            "paymentcategory", "receivablecategory", "downstreamcontractcategory",
            "expensecategory", "expensetype"
        ]
        
        for et in enum_types:
            try:
                await conn.execute(text(f"DROP TYPE IF EXISTS {et}"))
                print(f"Dropped type {et}")
            except Exception as e:
                print(f"Could not drop type {et}: {e}")

    print("Migration V1.2 Complete!")

if __name__ == "__main__":
    asyncio.run(migrate_v1_2())
