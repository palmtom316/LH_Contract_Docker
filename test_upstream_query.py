#!/usr/bin/env python3
"""
Test script to verify upstream contracts can be queried successfully
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

DATABASE_URL = "postgresql+asyncpg://lh_admin:dev_password_change_me@localhost:5432/lh_contract_db"

async def test_upstream_query():
    print("🔍 Testing upstream contracts query...")
    
    try:
        # Create engine
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        # Test connection
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM contracts_upstream"))
            count = result.scalar()
            print(f"✅ Database connection successful")
            print(f"✅ Found {count} upstream contracts in database")
            
            # Test column exists
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'contracts_upstream' 
                AND column_name IN ('contract_file_key', 'contract_file_storage', 'approval_pdf_key', 'approval_pdf_storage')
                ORDER BY column_name
            """))
            columns = [row[0] for row in result.all()]
            print(f"✅ MinIO columns found: {', '.join(columns)}")
            
            # Test actual query
            result = await conn.execute(text("""
                SELECT id, contract_code, contract_name, contract_file_key, contract_file_storage
                FROM contracts_upstream
                LIMIT 3
            """))
            rows = result.all()
            print(f"\n📋 Sample records:")
            for row in rows:
                print(f"  - ID: {row[0]}, Code: {row[1]}, Name: {row[2][:30]}...")
            
            print(f"\n✅ All tests passed! Database schema is correct.")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()

if __name__ == "__main__":
    result = asyncio.run(test_upstream_query())
    sys.exit(0 if result else 1)
