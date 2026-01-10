
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

DATABASE_URL = "postgresql+asyncpg://lh_admin:CHANGE_THIS_TO_A_STRONG_PASSWORD@localhost:5432/lh_contract_db"

async def check_columns():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'zero_hour_labor'"))
        columns = result.all()
        print("Columns in zero_hour_labor:")
        for col in columns:
            print(f"- {col[0]} ({col[1]})")

if __name__ == "__main__":
    asyncio.run(check_columns())
