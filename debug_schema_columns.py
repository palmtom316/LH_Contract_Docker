
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

# Use the credentials we discovered
DATABASE_URL = "postgresql+asyncpg://lh_admin:CHANGE_THIS_TO_A_STRONG_PASSWORD@localhost:5432/lh_contract_db"

TABLES = ["contracts_upstream", "contracts_downstream", "contracts_management"]

async def check_columns():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        for table in TABLES:
            print(f"\n--- {table} Columns ---")
            try:
                result = await conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'"))
                columns = result.all()
                for col in columns:
                    print(f"{col[0]}: {col[1]}")
            except Exception as e:
                print(f"Error checking {table}: {e}")

if __name__ == "__main__":
    asyncio.run(check_columns())
