
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

# Use the credentials we know
DATABASE_URL = "postgresql+asyncpg://lh_admin:CHANGE_THIS_TO_A_STRONG_PASSWORD@localhost:5432/lh_contract_db"

async def check_tables():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result.all()]
        print("Existing tables:", tables)
        if "zero_hour_labor" in tables:
            print("found zero_hour_labor")
        else:
            print("MISSING zero_hour_labor")

if __name__ == "__main__":
    asyncio.run(check_tables())
