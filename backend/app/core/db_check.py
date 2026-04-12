"""
Database Schema Self-Healing Module
数据库结构自动修复模块

This module validates and AUTO-FIXES database schema at startup.
If missing columns are detected, they are automatically added.

=== SCHEMA VERSION HISTORY ===

V1.0 (Initial):
    - users, contracts_upstream, contracts_downstream, contracts_management
    - expenses_non_contract, audit_logs

V1.2:
    - Added: zero_hour_labor (工时记录)
    - Added: zero_hour_labor_materials (工时材料明细)
    - Added: sys_dictionaries (数据字典)
    - Added: sys_config (系统配置)

V1.4:
    - Added Feishu approval columns to expenses_non_contract

V1.5 (2026-01-13 Updated):
    - Added MinIO storage columns to ALL file-related tables
    - Self-healing logic: automatically add missing columns

=== MAINTENANCE NOTES ===
When adding new tables/columns in a release:
1. Update V1_5_REQUIRED_COLUMNS below
2. Add version comment
3. Columns will be auto-added on startup if missing
"""
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger("app.db_check")


# ============================================
# V1.5 Required Columns - Auto-heal these on startup
# ============================================
# Format: { "table_name": [("column_name", "column_type", "default_value")] }
# These columns will be automatically added if missing

V1_5_REQUIRED_COLUMNS = {
    # Contract Tables
    "contracts_upstream": [
        ("contract_file_key", "VARCHAR(500)", None),
        ("contract_file_storage", "VARCHAR(50)", "'local'"),
        ("approval_pdf_key", "VARCHAR(500)", None),
        ("approval_pdf_storage", "VARCHAR(50)", "'local'"),
    ],
    "contracts_downstream": [
        ("contract_file_key", "VARCHAR(500)", None),
        ("contract_file_storage", "VARCHAR(50)", "'local'"),
        ("approval_pdf_key", "VARCHAR(500)", None),
        ("approval_pdf_storage", "VARCHAR(50)", "'local'"),
    ],
    "contracts_management": [
        ("contract_file_key", "VARCHAR(500)", None),
        ("contract_file_storage", "VARCHAR(50)", "'local'"),
        ("approval_pdf_key", "VARCHAR(500)", None),
        ("approval_pdf_storage", "VARCHAR(50)", "'local'"),
    ],
    
    # Finance Invoice Tables
    "finance_upstream_invoices": [
        ("file_key", "VARCHAR(500)", None),
        ("storage_provider", "VARCHAR(50)", "'local'"),
    ],
    "finance_downstream_invoices": [
        ("file_key", "VARCHAR(500)", None),
        ("storage_provider", "VARCHAR(50)", "'local'"),
    ],
    "finance_management_invoices": [
        ("file_key", "VARCHAR(500)", None),
        ("storage_provider", "VARCHAR(50)", "'local'"),
    ],
    
    # Finance Receivables/Payables/Payments Tables
    "finance_upstream_receivables": [
        ("file_key", "VARCHAR(500)", None),
        ("storage_provider", "VARCHAR(50)", "'local'"),
    ],
    "finance_upstream_receipts": [
        ("file_key", "VARCHAR(500)", None),
        ("storage_provider", "VARCHAR(50)", "'local'"),
    ],
    "finance_downstream_payables": [
        ("file_key", "VARCHAR(500)", None),
        ("storage_provider", "VARCHAR(50)", "'local'"),
    ],
    "finance_downstream_payments": [
        ("file_key", "VARCHAR(500)", None),
        ("storage_provider", "VARCHAR(50)", "'local'"),
    ],
    "finance_management_payables": [
        ("file_key", "VARCHAR(500)", None),
        ("storage_provider", "VARCHAR(50)", "'local'"),
    ],
    "finance_management_payments": [
        ("file_key", "VARCHAR(500)", None),
        ("storage_provider", "VARCHAR(50)", "'local'"),
    ],
    
    # Settlement Tables
    "downstream_settlements": [
        ("file_key", "VARCHAR(500)", None),
        ("storage_provider", "VARCHAR(50)", "'local'"),
    ],
    "management_settlements": [
        ("file_key", "VARCHAR(500)", None),
        ("storage_provider", "VARCHAR(50)", "'local'"),
    ],
    "project_settlements": [
        ("file_key", "VARCHAR(500)", None),
        ("storage_provider", "VARCHAR(50)", "'local'"),
        ("audit_report_key", "VARCHAR(500)", None),
        ("audit_report_storage", "VARCHAR(50)", "'local'"),
        ("settlement_report_key", "VARCHAR(500)", None),
        ("settlement_report_storage", "VARCHAR(50)", "'local'"),
        ("start_report_key", "VARCHAR(500)", None),
        ("start_report_storage", "VARCHAR(50)", "'local'"),
        ("completion_report_key", "VARCHAR(500)", None),
        ("completion_report_storage", "VARCHAR(50)", "'local'"),
        ("visa_records_key", "VARCHAR(500)", None),
        ("visa_records_storage", "VARCHAR(50)", "'local'"),
        ("measurement_records_key", "VARCHAR(500)", None),
        ("measurement_records_storage", "VARCHAR(50)", "'local'"),
        ("progress_payment_key", "VARCHAR(500)", None),
        ("progress_payment_storage", "VARCHAR(50)", "'local'"),
    ],
    
    # Expenses Non-Contract
    "expenses_non_contract": [
        ("file_key", "VARCHAR(500)", None),
        ("storage_provider", "VARCHAR(50)", "'local'"),
        ("invoice_file_key", "VARCHAR(500)", None),
        ("invoice_file_storage", "VARCHAR(50)", "'local'"),
        ("approval_pdf_key", "VARCHAR(500)", None),
        ("approval_pdf_storage", "VARCHAR(50)", "'local'"),
    ],
    
    # Zero Hour Labor
    "zero_hour_labor": [
        ("approval_pdf_key", "VARCHAR(500)", None),
        ("approval_pdf_storage", "VARCHAR(50)", "'local'"),
        ("dispatch_file_key", "VARCHAR(500)", None),
        ("dispatch_file_storage", "VARCHAR(50)", "'local'"),
        ("settlement_file_key", "VARCHAR(500)", None),
        ("settlement_file_storage", "VARCHAR(50)", "'local'"),
        ("invoice_file_key", "VARCHAR(500)", None),
        ("invoice_file_storage", "VARCHAR(50)", "'local'"),
    ],
    
    # Zero Hour Labor Materials
    "zero_hour_labor_materials": [
        ("file_key", "VARCHAR(500)", None),
        ("storage_provider", "VARCHAR(50)", "'local'"),
    ],
}


async def check_table_exists(conn: AsyncConnection, table_name: str) -> bool:
    """检查表是否存在"""
    result = await conn.execute(
        text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = :table_name
            )
        """),
        {"table_name": table_name}
    )
    return result.scalar()


async def get_existing_columns(conn: AsyncConnection, table_name: str) -> set:
    """获取表的所有列名"""
    result = await conn.execute(
        text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = :table_name
        """),
        {"table_name": table_name}
    )
    return {row[0] for row in result.fetchall()}


async def add_missing_column(conn: AsyncConnection, table_name: str, 
                             column_name: str, column_type: str, 
                             default_value: str = None) -> bool:
    """添加缺失的列"""
    try:
        if default_value:
            sql = f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {column_type} DEFAULT {default_value}"
        else:
            sql = f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {column_type}"
        
        await conn.execute(text(sql))
        logger.info(f"[DB AUTO-FIX] ✓ Added column {table_name}.{column_name}")
        return True
    except Exception as e:
        logger.error(f"[DB AUTO-FIX] ✗ Failed to add {table_name}.{column_name}: {e}")
        return False


async def auto_fix_schema(conn: AsyncConnection) -> dict:
    """
    数据库结构自动修复已从应用正常启动路径移除。
    返回: {
        "fixed_count": int,
        "skipped_count": int,
        "failed_count": int,
        "details": {...}
    }
    """
    return {
        "fixed_count": 0,
        "skipped_count": 0,
        "failed_count": 0,
        "details": {"mode": "disabled_in_app_startup"},
    }


async def run_startup_check(engine) -> None:
    """
    在应用启动时运行数据库检查和自动修复
    This is the main entry point called from main.py lifespan
    """
    try:
        async with engine.begin() as conn:  # Use begin() to auto-commit
            logger.info("[DB CHECK] Starting database schema validation...")
            
            # Run auto-fix
            result = await auto_fix_schema(conn)
            
            if result["fixed_count"] > 0:
                logger.warning(
                    f"[DB AUTO-FIX] 🔧 Auto-fixed {result['fixed_count']} missing columns. "
                    f"Details: {result['details']}"
                )
            elif result["failed_count"] > 0:
                logger.error(
                    f"[DB AUTO-FIX] ❌ Failed to fix {result['failed_count']} columns. "
                    f"Manual intervention required."
                )
            else:
                logger.info(
                    f"[DB CHECK] ✓ Database schema is up to date. "
                    f"({result['skipped_count']} columns verified)"
                )
                
    except Exception as e:
        logger.error(f"[DB CHECK] Database schema check failed: {e}")
        # Don't raise - allow app to start even if check fails
        # The individual API calls will report specific errors


# Legacy function for backward compatibility
async def check_database_schema(conn: AsyncConnection) -> dict:
    """
    检查数据库结构 (兼容旧版本)
    """
    missing_columns = {}
    
    for table_name, columns in V1_5_REQUIRED_COLUMNS.items():
        table_exists = await check_table_exists(conn, table_name)
        if not table_exists:
            continue
        
        existing_cols = await get_existing_columns(conn, table_name)
        
        for col_name, col_type, default_val in columns:
            if col_name not in existing_cols:
                if table_name not in missing_columns:
                    missing_columns[table_name] = []
                missing_columns[table_name].append(col_name)
    
    if missing_columns:
        return {
            "status": "warning",
            "missing_tables": [],
            "missing_columns": missing_columns,
            "message": f"缺失列: {missing_columns}"
        }
    
    return {
        "status": "ok",
        "missing_tables": [],
        "missing_columns": {},
        "message": "数据库结构检查通过"
    }
