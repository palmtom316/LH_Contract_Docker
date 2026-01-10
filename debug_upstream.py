
import asyncio
import traceback
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy import select, func, desc
from app.models.contract_upstream import ContractUpstream
from app.models.zero_hour_labor import ZeroHourLabor # Import to ensure registry is complete?

# Credentials
DATABASE_URL = "postgresql+asyncpg://lh_admin:CHANGE_THIS_TO_A_STRONG_PASSWORD@localhost:5432/lh_contract_db"

async def debug_query():
    print("Connecting...")
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("Session created. Building query...")
        try:
            # Replicate list_contracts query
            query = select(ContractUpstream).options(
                selectinload(ContractUpstream.receivables),
                selectinload(ContractUpstream.invoices),
                selectinload(ContractUpstream.receipts),
                selectinload(ContractUpstream.settlements)
            )
            # Add limit
            query = query.limit(5)
            
            print("Executing query...")
            result = await session.execute(query)
            print("Query executed.")
            contracts = result.scalars().all()
            print(f"Found {len(contracts)} contracts.")
            for c in contracts:
                print(f"ID: {c.id}, Code: {c.contract_code}")
                
        except Exception as e:
            with open("db_error.txt", "w") as f:
                traceback.print_exc(file=f)
            print("Error written to db_error.txt")

if __name__ == "__main__":
    asyncio.run(debug_query())
