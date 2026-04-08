
import asyncio
import os
import urllib.request
import urllib.error
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# DB Config
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://lh_admin:<replace-me>@localhost:5432/lh_contract_db",
)

# API Config
API_URL = "http://localhost:8000/health"

async def check_db_connection():
    print("Checking DB connection string from DATABASE_URL")
    try:
        engine = create_async_engine(DATABASE_URL)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"DB Connection successful: {result.scalar()}")
        await engine.dispose()
    except Exception as e:
        print(f"DB Connection failed: {e}")

def check_api_connection():
    print(f"Checking API connection: {API_URL}")
    try:
        with urllib.request.urlopen(API_URL) as response:
            print(f"API Connection successful: {response.status} {response.read().decode('utf-8')}")
    except urllib.error.URLError as e:
        print(f"API Connection failed: {e}")
    except Exception as e:
        print(f"API Check failed with error: {e}")

async def main():
    print("--- Starting Connectivity Checks ---")
    await check_db_connection()
    check_api_connection()
    print("--- Checks Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
