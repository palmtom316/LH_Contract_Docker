"""
Apply Performance Indexes to Database
Run this script to create optimized indexes for query performance
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from app.database import engine
from app.core.db_indexes import SQL_SCRIPT


async def apply_indexes():
    """Apply all performance indexes"""
    print("🔧 Applying performance indexes...")

    statements = [
        s.strip()
        for s in SQL_SCRIPT.split(';')
        if s.strip() and not s.strip().startswith('--')
    ]

    success_count = 0
    error_count = 0

    async with engine.begin() as conn:
        for stmt in statements:
            if not stmt or len(stmt) < 10:
                continue

            try:
                await conn.execute(text(stmt))
                success_count += 1
                # Extract index name for logging
                if 'CREATE INDEX' in stmt:
                    idx_name = stmt.split('IF NOT EXISTS')[1].split('ON')[0].strip() if 'IF NOT EXISTS' in stmt else 'unknown'
                    print(f"✓ Created index: {idx_name}")
                elif 'ANALYZE' in stmt:
                    table_name = stmt.replace('ANALYZE', '').strip().rstrip(';')
                    print(f"✓ Analyzed table: {table_name}")
            except Exception as e:
                error_count += 1
                print(f"✗ Error: {str(e)[:100]}")

    print(f"\n📊 Summary:")
    print(f"   Success: {success_count}")
    print(f"   Errors: {error_count}")
    print(f"   Total: {success_count + error_count}")

    if error_count == 0:
        print("\n✅ All indexes applied successfully!")
    else:
        print(f"\n⚠️  Completed with {error_count} errors")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(apply_indexes())
