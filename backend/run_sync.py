"""
Feishu Sync Worker Entry Point

This script runs as a standalone background worker to sync contract data
to Feishu Base (多维表格) on a scheduled interval.

Usage:
    python run_sync.py

Configuration via environment variables:
- FEISHU_APP_ID: Feishu App ID
- FEISHU_APP_SECRET: Feishu App Secret
- FEISHU_BASE_APP_TOKEN: Base App Token
- FEISHU_BASE_TABLE_ID: Table ID
- DATABASE_URL: PostgreSQL connection string
"""
import os
import sys
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("sync_worker")

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
except ImportError:
    logger.error("APScheduler not installed. Run: pip install apscheduler")
    sys.exit(1)


def get_missing_required_vars() -> list[str]:
    """Return missing environment variables required for Feishu sync."""
    required_vars = [
        "FEISHU_APP_ID",
        "FEISHU_APP_SECRET",
        "FEISHU_BASE_APP_TOKEN",
        "FEISHU_BASE_TABLE_ID",
        "DATABASE_URL",
    ]
    return [name for name in required_vars if not os.getenv(name)]


async def sync_job():
    """Wrapper for the sync function with error handling"""
    logger.info("=== Starting scheduled sync job ===")
    try:
        from app.services.feishu_service import sync_contracts_to_base
        await sync_contracts_to_base()
        logger.info("=== Sync job completed successfully ===")
    except Exception as e:
        logger.error(f"=== Sync job failed: {e} ===", exc_info=True)


def run_sync_job():
    """Synchronous wrapper for the async job"""
    asyncio.get_event_loop().run_until_complete(sync_job())


def main():
    """Main entry point for the sync worker"""
    logger.info("=" * 50)
    logger.info("Feishu Sync Worker Starting")
    logger.info("=" * 50)
    
    missing = get_missing_required_vars()
    if missing:
        logger.warning(f"Missing environment variables: {missing}")
        logger.warning("Sync worker will stay idle until Feishu configuration is complete")
    
    # Create scheduler
    scheduler = AsyncIOScheduler()
    
    if missing:
        logger.info("Scheduler configured in idle mode")
    else:
        # Run sync every 60 minutes
        scheduler.add_job(
            sync_job,
            'interval',
            minutes=60,
            id='contract_sync',
            name='Sync contracts to Feishu Base'
        )

        # Also run immediately on startup
        scheduler.add_job(
            sync_job,
            'date',
            id='initial_sync',
            name='Initial contract sync'
        )

        logger.info("Scheduler configured: Sync every 60 minutes")
    logger.info("Starting scheduler...")
    
    scheduler.start()
    
    # Keep the worker running
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Sync worker shutting down...")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
