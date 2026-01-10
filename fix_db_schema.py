
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

DATABASE_URL = "postgresql+asyncpg://lh_admin:CHANGE_THIS_TO_A_STRONG_PASSWORD@localhost:5432/lh_contract_db"

# Tables and their columns to check/add
SCHEMA_UPDATES = {
    "contracts_upstream": [
        ("contract_handler", "VARCHAR(100)"),
        ("archive_number", "VARCHAR(100)"),
        ("approval_status", "VARCHAR(50) DEFAULT 'DRAFT'"),
        ("feishu_instance_code", "VARCHAR(100)"),
        ("approval_pdf_path", "VARCHAR(500)")
    ],
    "contracts_downstream": [
        ("contract_handler", "VARCHAR(100)"),
        ("contract_manager", "VARCHAR(100)"),
        ("category", "VARCHAR(50)"),
        ("company_category", "VARCHAR(50)"),
        ("pricing_mode", "VARCHAR(100)"),
        ("management_mode", "VARCHAR(100)"),
        ("approval_status", "VARCHAR(50) DEFAULT 'DRAFT'"),
        ("feishu_instance_code", "VARCHAR(100)"),
        ("approval_pdf_path", "VARCHAR(500)"),
        # Ensure older fields if needed, but error was specific to new ones
    ],
    "contracts_management": [
        ("contract_handler", "VARCHAR(100)"),
        ("contract_manager", "VARCHAR(100)"),
        ("category", "VARCHAR(50)"),
        ("company_category", "VARCHAR(50)"),
        ("pricing_mode", "VARCHAR(100)"),
        ("management_mode", "VARCHAR(100)"),
        ("approval_status", "VARCHAR(50) DEFAULT 'DRAFT'"),
        ("feishu_instance_code", "VARCHAR(100)"),
        ("approval_pdf_path", "VARCHAR(500)")
    ]
}

async def fix_schema():
    print("Connecting to DB...")
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.connect() as conn:
        for table_name, columns in SCHEMA_UPDATES.items():
            print(f"\nProcessing table: {table_name}")
            # Check if table exists first (sanity check)
            res = await conn.execute(text(f"SELECT to_regclass('{table_name}')"))
            if not res.scalar():
                print(f"Table {table_name} does not exist. Skipping.")
                continue

            # Get existing columns
            result = await conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'"))
            existing_cols = [row[0] for row in result.all()]
            # print(f"Existing columns: {existing_cols}")
            
            # Add missing columns
            for col_name, col_type in columns:
                if col_name not in existing_cols:
                    print(f"Adding missing column: {col_name} ({col_type})")
                    try:
                        await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                        print(f"Added {col_name} successfully.")
                    except Exception as e:
                        print(f"Failed to add {col_name}: {e}")
                else:
                    print(f"Column {col_name} already exists.")
        
        await conn.commit()
        print("\nSchema fix complete.")

if __name__ == "__main__":
    asyncio.run(fix_schema())
