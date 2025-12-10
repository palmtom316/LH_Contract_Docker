import sys
import os
import asyncio
from sqlalchemy import select

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.models.user import User
from app.services.auth import verify_password

async def main():
    try:
        async with AsyncSessionLocal() as session:
            print("Searching for user 'admin'...")
            result = await session.execute(select(User).where(User.username == 'admin'))
            user = result.scalar_one_or_none()
            if not user:
                print("User 'admin' not found!")
                return
            
            print(f"User found: {user.username}, Role: {user.role}")
            print(f"Hashed Pwd Length: {len(user.hashed_password)}")
            
            pwd = "admin123"
            print(f"Verifying password '{pwd}'...")
            try:
                valid = verify_password(pwd, user.hashed_password)
                print(f"Result: {valid}")
            except Exception as e:
                print(f"ERROR verifying password: {e}")

    except Exception as e:
        print(f"Database Error: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
