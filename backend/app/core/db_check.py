"""
Database Schema Validation Module
检查数据库结构与应用程序模型是否匹配

This module validates that the database schema matches the application models
at startup. It is crucial for detecting missing tables or columns after upgrades.

=== SCHEMA VERSION HISTORY ===

V1.0 (Initial):
    - users, contracts_upstream, contracts_downstream, contracts_management
    - expenses_non_contract, audit_logs

V1.2:
    - Added: zero_hour_labor (工时记录)
    - Added: zero_hour_labor_materials (工时材料明细)
    - Added: sys_dictionaries (数据字典)
    - Added: sys_config (系统配置)
    - New columns in zero_hour_labor:
        dispatch_file_path, skilled_unit_price, skilled_quantity, skilled_price_total,
        general_unit_price, general_quantity, general_price_total

V1.4:
    - Added Feishu approval columns to expenses_non_contract:
        approval_status, feishu_instance_code, approval_pdf_path

=== MAINTENANCE NOTES ===
When adding new tables/columns in a release:
1. Update EXPECTED_COLUMNS below
2. Add version comment (e.g., "# V1.5 新增")
3. Create corresponding Alembic migration
4. Update this docstring with version history
"""
import logging
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger("app.db_check")


# 定义预期的表结构 - 每次版本更新时需要更新此列表
# See module docstring for version history
EXPECTED_COLUMNS = {
    "zero_hour_labor": [
        ("id", "integer"),
        ("labor_date", "date"),
        ("attribution", "character varying"),
        ("upstream_contract_id", "integer"),
        ("dispatch_unit", "character varying"),
        ("dispatch_file_path", "character varying"),  # V1.2 新增
        ("skilled_unit_price", "numeric"),  # V1.2 新增
        ("skilled_quantity", "numeric"),  # V1.2 新增
        ("skilled_price_total", "numeric"),  # V1.2 新增
        ("general_unit_price", "numeric"),  # V1.2 新增
        ("general_quantity", "numeric"),  # V1.2 新增
        ("general_price_total", "numeric"),  # V1.2 新增
        ("labor_type", "character varying"),
        ("labor_unit_price", "numeric"),
        ("labor_quantity", "numeric"),
        ("labor_price_total", "numeric"),
        ("vehicle_quantity", "numeric"),
        ("vehicle_unit_price", "numeric"),
        ("vehicle_price_total", "numeric"),
        ("total_amount", "numeric"),
        ("created_at", "timestamp"),
        ("updated_at", "timestamp"),
        ("created_by", "integer"),
    ],
    "zero_hour_labor_materials": [  # V1.2 新增表
        ("id", "integer"),
        ("zero_hour_labor_id", "integer"),
        ("material_name", "character varying"),
        ("material_unit", "character varying"),
        ("material_quantity", "numeric"),
        ("material_unit_price", "numeric"),
        ("material_price_total", "numeric"),
    ],
    "sys_dictionaries": [  # V1.2 新增表
        ("id", "integer"),
        ("category", "character varying"),
        ("label", "character varying"),
        ("value", "character varying"),
        ("sort_order", "integer"),
        ("is_active", "boolean"),
    ],
    "sys_config": [  # V1.2 新增表
        ("id", "integer"),
        ("key", "character varying"),
        ("value", "text"),
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


async def get_table_columns(conn: AsyncConnection, table_name: str) -> list:
    """获取表的所有列"""
    result = await conn.execute(
        text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = :table_name
        """),
        {"table_name": table_name}
    )
    return [(row[0], row[1]) for row in result.fetchall()]


async def check_database_schema(conn: AsyncConnection) -> dict:
    """
    检查数据库结构
    返回: {
        "status": "ok" | "warning" | "error",
        "missing_tables": [...],
        "missing_columns": {"table": ["col1", "col2"]},
        "message": "..."
    }
    """
    missing_tables = []
    missing_columns = {}
    
    for table_name, expected_cols in EXPECTED_COLUMNS.items():
        # 检查表是否存在
        table_exists = await check_table_exists(conn, table_name)
        
        if not table_exists:
            missing_tables.append(table_name)
            continue
        
        # 检查列是否存在
        existing_cols = await get_table_columns(conn, table_name)
        existing_col_names = {col[0] for col in existing_cols}
        
        for col_name, col_type in expected_cols:
            if col_name not in existing_col_names:
                if table_name not in missing_columns:
                    missing_columns[table_name] = []
                missing_columns[table_name].append(col_name)
    
    # 生成结果
    if missing_tables or missing_columns:
        status = "error" if missing_tables else "warning"
        message_parts = []
        
        if missing_tables:
            message_parts.append(f"缺失表: {', '.join(missing_tables)}")
        
        if missing_columns:
            for table, cols in missing_columns.items():
                message_parts.append(f"表 {table} 缺失列: {', '.join(cols)}")
        
        message = "; ".join(message_parts)
        message += " - 请执行数据库迁移脚本: scripts/migrate_v1_2_complete.sql"
        
        return {
            "status": status,
            "missing_tables": missing_tables,
            "missing_columns": missing_columns,
            "message": message
        }
    
    return {
        "status": "ok",
        "missing_tables": [],
        "missing_columns": {},
        "message": "数据库结构检查通过"
    }


async def run_startup_check(engine) -> None:
    """
    在应用启动时运行数据库检查
    如果发现问题，记录警告日志
    """
    try:
        async with engine.connect() as conn:
            result = await check_database_schema(conn)
            
            if result["status"] == "ok":
                logger.info("[DB CHECK] " + result["message"])
            elif result["status"] == "warning":
                logger.warning("[DB CHECK] ⚠️ " + result["message"])
            else:
                logger.error("[DB CHECK] ❌ " + result["message"])
                
    except Exception as e:
        logger.error(f"[DB CHECK] 数据库检查失败: {e}")
