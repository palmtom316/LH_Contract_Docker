"""
V1.4 Feishu Migration Script - Part 2
Run this to add approval columns to the expense (expenses_non_contract) table
"""
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Try with the password from .env file (CHANGE_THIS_TO_A_STRONG_PASSWORD)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://lh_admin:CHANGE_THIS_TO_A_STRONG_PASSWORD@localhost:5432/lh_contract_db"
)

MIGRATIONS = [
    # Expense Non Contract
    "ALTER TABLE expenses_non_contract ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50) DEFAULT 'DRAFT'",
    "ALTER TABLE expenses_non_contract ADD COLUMN IF NOT EXISTS feishu_instance_code VARCHAR(100)",
    "ALTER TABLE expenses_non_contract ADD COLUMN IF NOT EXISTS approval_pdf_path VARCHAR(500)",
]

async def run_migration():
    print(f"Connecting to: {DATABASE_URL.split('@')[1]}")
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        for sql in MIGRATIONS:
            print(f"Running: {sql[:60]}...")
            await conn.execute(text(sql))
    
    await engine.dispose()
    print("Migration for expenses completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_migration())
