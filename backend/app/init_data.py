from sqlalchemy import select
from app.models.user import User
from app.services.auth import get_password_hash
from app.database import AsyncSessionLocal

async def init_data():
    """Initialize data if not present (create admin user)"""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(User).where(User.username == "admin"))
            user = result.scalar_one_or_none()
            
            if not user:
                print("✨ Creating default admin user (admin/admin123)...")
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    full_name="Administrator",
                    hashed_password=get_password_hash("admin123"),
                    is_active=True,
                    is_superuser=True
                )
                db.add(admin_user)
                await db.commit()
                print("✅ Default admin user created.")
            else:
                print("👌 Admin user already exists.")
        except Exception as e:
            print(f"❌ Error initializing data: {e}")
            await db.rollback()
