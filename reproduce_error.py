
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.contract_upstream import ContractUpstream
from app.models.contract_downstream import ContractDownstream
from app.models.contract_management import ContractManagement
from app.database import Base

# Use the credentials we discovered
DATABASE_URL = "postgresql+asyncpg://lh_admin:CHANGE_THIS_TO_A_STRONG_PASSWORD@localhost:5432/lh_contract_db"

async def reproduce():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("Checking Upstream...")
        try:
            stmt = select(ContractUpstream).limit(1)
            result = await session.execute(stmt)
            print("Upstream success")
        except Exception as e:
            print(f"Upstream FALIED: {e}")

        print("Checking Downstream...")
        try:
            stmt = select(ContractDownstream).limit(1)
            result = await session.execute(stmt)
            print("Downstream success")
        except Exception as e:
            print(f"Downstream FALIED: {e}")

        print("Checking Management...")
        try:
            stmt = select(ContractManagement).limit(1)
            result = await session.execute(stmt)
            print("Management success")
        except Exception as e:
            print(f"Management FALIED: {e}")

if __name__ == "__main__":
    asyncio.run(reproduce())
