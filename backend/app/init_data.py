from sqlalchemy import select
import logging

from app.models.user import User
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def init_data():
    """Startup initialization without creating unsafe default accounts."""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(User.id).limit(1))
            if result.scalar_one_or_none() is None:
                logger.warning(
                    "No users found during startup. Automatic admin bootstrap is disabled; "
                    "use /api/v1/auth/init-admin with INIT_ADMIN_TOKEN in an explicit init window."
                )
            else:
                logger.info("User data already initialized; skipping bootstrap.")
        except Exception as e:
            logger.error("Error checking bootstrap state: %s", e)
            await db.rollback()
