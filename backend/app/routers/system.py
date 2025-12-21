from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from app.services.auth import get_current_active_user
from app.models.user import User
from app.config import settings
import shutil
import subprocess
import os
from datetime import datetime
from typing import List
from urllib.parse import urlparse, unquote
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from app.database import get_db
from app.models.system import SysDictionary, SystemConfig

router = APIRouter()

def find_pg_dump():
    """Find pg_dump executable in PATH or common Windows locations"""
    if shutil.which("pg_dump"):
        return "pg_dump"
    
    # Common Windows paths
    possible_versions = [17, 16, 15, 14, 13, 12, 11, 10]
    common_paths = []
    
    for v in possible_versions:
        common_paths.append(rf"C:\Program Files\PostgreSQL\{v}\bin\pg_dump.exe")
        common_paths.append(rf"C:\Program Files (x86)\PostgreSQL\{v}\bin\pg_dump.exe")
        
    for p in common_paths:
        if os.path.exists(p):
            return p
    return None

def get_pg_dump_cmd(db_url: str, output_file: str):
    """
    Construct pg_dump command from sqlalchemy url
    input: postgresql+asyncpg://user:pass@host:port/dbname
    """
    pg_dump_exe = find_pg_dump()
    if not pg_dump_exe:
        raise HTTPException(status_code=500, detail="未找到 pg_dump 工具，无法进行备份。请安装 PostgreSQL 客户端。")

    # Remove driver part
    clean_url = db_url.replace("+asyncpg", "")
    
    # pg_dump needs standard URI
    # Use -d flag to explicitly specify connection string to avoid argument parsing ambiguity
    cmd = [pg_dump_exe, "-d", clean_url, "-f", output_file]
    return cmd

def run_db_dump(output_file: str):
    """Helper to run pg_dump with proper environment"""
    cmd = get_pg_dump_cmd(settings.DATABASE_URL, output_file)
    
    # Prepare environment with PGPASSWORD
    env = os.environ.copy()
    try:
        clean_token = settings.DATABASE_URL.replace("+asyncpg", "")
        parsed = urlparse(clean_token)
        if parsed.password:
            env["PGPASSWORD"] = unquote(parsed.password)
    except Exception as e:
        print(f"Password parsing warning: {e}")

    # Execute pg_dump
    try:
        subprocess.run(
            cmd, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            env=env
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode(errors='ignore') if e.stderr else str(e)
        raise Exception(error_msg)

@router.get("/backup/db")
async def backup_database(
    current_user: User = Depends(get_current_active_user)
):
    """
    Backup database to SQL file and return it
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"lh_contract_db_{timestamp}.sql"
    filepath = os.path.join(settings.UPLOAD_DIR, "temp", filename)
    
    # Ensure temp dir exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    try:
        run_db_dump(filepath)
        
        return FileResponse(
            path=filepath, 
            filename=filename, 
            media_type='application/sql'
        )
        
    except Exception as e:
        print(f"Backup error: {str(e)}")
        # Check if it is our custom error detail or generic
        detail_msg = f"数据库备份失败: {str(e)}"
        raise HTTPException(status_code=500, detail=detail_msg)


@router.get("/backup/full")
async def backup_system(
    current_user: User = Depends(get_current_active_user)
):
    """
    Full system backup: Database + Uploaded files (ZIP)
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"lh_system_backup_{timestamp}"
    temp_dir = os.path.join(settings.UPLOAD_DIR, "temp", base_filename)
    zip_filename = f"{base_filename}.zip"
    zip_filepath = os.path.join(settings.UPLOAD_DIR, "temp", zip_filename)
    
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # 1. Dump Database
        db_file = os.path.join(temp_dir, "database.sql")
        run_db_dump(db_file)
        
        # 2. Copy Uploads
        uploads_src = settings.UPLOAD_DIR
        uploads_dst = os.path.join(temp_dir, "uploads")
        
        def ignore_patterns(path, names):
            if path == settings.UPLOAD_DIR:
                return {'temp'}
            return set()

        if os.path.exists(uploads_src):
             shutil.copytree(uploads_src, uploads_dst, ignore=ignore_patterns)

        # 3. Create ZIP
        shutil.make_archive(os.path.join(settings.UPLOAD_DIR, "temp", base_filename), 'zip', temp_dir)
        
        # 4. Cleanup temp folder (keep zip)
        shutil.rmtree(temp_dir)
        
        return FileResponse(
            path=zip_filepath,
            filename=zip_filename,
            media_type='application/zip'
        )

    except Exception as e:
        print(f"Full backup error: {str(e)}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=f"系统备份失败: {str(e)}")

@router.post("/logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload system logo
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")
    
    # Save to uploads/system/logo.png
    system_dir = os.path.join(settings.UPLOAD_DIR, "system")
    os.makedirs(system_dir, exist_ok=True)
    
    # We always save as logo.png or preserve extension? 
    # For simplicity, let's keep original extension or convert to png.
    # Frontend layout expects a fixed URL or we return the dynamic URL.
    # Let's save as specific name 'site_logo.png' (or match extension)
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
        ext = '.png' # Default fallback
        
    filename = f"site_logo{ext}"
    target_path = os.path.join(system_dir, filename)
    
    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Also clean up other logo files to avoid confusion if we change extension
        for other_ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
            if other_ext != ext:
                other_path = os.path.join(system_dir, f"site_logo{other_ext}")
                if os.path.exists(other_path):
                    os.remove(other_path)
                    
        return {"message": "Logo上传成功", "path": f"/uploads/system/{filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logo上传失败: {str(e)}")

@router.get("/logo")
async def get_logo():
    """
    Get current system logo URL
    """
    system_dir = os.path.join(settings.UPLOAD_DIR, "system")
    if not os.path.exists(system_dir):
        return {"path": None}
        
    # Find existing logo
    for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
        filename = f"site_logo{ext}"
        if os.path.exists(os.path.join(system_dir, filename)):
            return {"path": f"/uploads/system/{filename}"}
            
    return {"path": None}

# --- System Configuration & Dictionary Endpoints ---

class SystemConfigUpdate(BaseModel):
    system_name: str | None = None
    # Add other config fields if needed

@router.get("/config")
async def get_system_config(
    db: AsyncSession = Depends(get_db)
):
    """Get system configuration (name, logo, etc)"""
    # Fetch all config
    result = await db.execute(select(SystemConfig))
    configs = result.scalars().all()
    
    config_dict = {
        "system_name": "Lanhai Contract System",
        "system_logo": None 
    }
    
    # Override defaults
    for c in configs:
        if c.key in config_dict:
            config_dict[c.key] = c.value
            
    # Check logo file existence logic if needed, but simple return is fine
    # Re-use the logic from get_logo if possible, but distinct is fine
    if not config_dict["system_logo"]:
        pass

    return config_dict

@router.post("/config")
async def update_system_config(
    config: SystemConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update system configuration"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Need admin privileges")
        
    if config.system_name is not None:
        # Upsert
        result = await db.execute(select(SystemConfig).where(SystemConfig.key == "system_name"))
        obj = result.scalar_one_or_none()
        if obj:
            obj.value = config.system_name
        else:
            db.add(SystemConfig(key="system_name", value=config.system_name))
            
    await db.commit()
    return {"message": "Configuration updated"}

# --- Dictionary Endpoints ---

class OptionCreate(BaseModel):
    category: str
    label: str
    value: str
    sort_order: int = 0

class OptionUpdate(BaseModel):
    label: str | None = None
    value: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None

@router.get("/options")
async def get_all_options(
    category: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """Get options, optionally filtered by category"""
    stmt = select(SysDictionary).where(SysDictionary.is_active == True).order_by(SysDictionary.sort_order)
    if category:
        stmt = stmt.where(SysDictionary.category == category)
        
    result = await db.execute(stmt)
    options = result.scalars().all()
    return options

@router.post("/options")
async def create_option(
    option: OptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new dictionary option"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Need admin privileges")
        
    # Check duplicate in category
    res = await db.execute(select(SysDictionary).where(
        SysDictionary.category == option.category,
        SysDictionary.value == option.value
    ))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Option value already exists in this category")
        
    new_opt = SysDictionary(
        category=option.category,
        label=option.label,
        value=option.value,
        sort_order=option.sort_order
    )
    db.add(new_opt)
    await db.commit()
    await db.refresh(new_opt)
    return new_opt

@router.put("/options/{id}")
async def update_option(
    id: int,
    option: OptionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an option"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Need admin privileges")
        
    res = await db.execute(select(SysDictionary).where(SysDictionary.id == id))
    obj = res.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Option not found")
        
    if option.label is not None: obj.label = option.label
    if option.value is not None: obj.value = option.value
    if option.sort_order is not None: obj.sort_order = option.sort_order
    if option.is_active is not None: obj.is_active = option.is_active
    
    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/options/{id}")
async def delete_option(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete (Hard delete) an option"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Need admin privileges")
        
    res = await db.execute(select(SysDictionary).where(SysDictionary.id == id))
    obj = res.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Option not found")
        
    await db.delete(obj)
    await db.commit()
    return {"message": "Option deleted"}


@router.post("/reset")
async def reset_system(
    confirm_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Reset system to initial state.
    WARNING: This will delete ALL data except superusers.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Need admin privileges")
        
    if confirm_code != "RESET":
        raise HTTPException(status_code=400, detail="Invalid confirmation code")

    try:
        from sqlalchemy import text
        # 1. Truncate business tables
        # Use CASCADE to handle foreign keys
        target_tables = [
             "finance_upstream_receivables", "finance_upstream_invoices", "finance_upstream_receipts", "project_settlements",
             "finance_downstream_payables", "finance_downstream_invoices", "finance_downstream_payments", "downstream_settlements",
             "finance_management_payables", "finance_management_invoices", "finance_management_payments", "management_settlements",
             "contracts_upstream", "contracts_downstream", "contracts_management",
             "sys_expenses", "sys_audit_log", "sys_files"
        ]
        
        # Check which tables exist to avoid "table does not exist" error which aborts transaction
        # Postgres specific
        result = await db.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        ))
        existing_tables_rows = result.fetchall()
        existing_tables = {row[0] for row in existing_tables_rows}
        
        tables_to_truncate = [t for t in target_tables if t in existing_tables]
        
        if tables_to_truncate:
             truncate_sql = f"TRUNCATE TABLE {', '.join(tables_to_truncate)} CASCADE"
             await db.execute(text(truncate_sql))

        # 2. Delete Users (except superusers)
        await db.execute(text("DELETE FROM users WHERE is_superuser = false"))
        
        # 3. Clear Uploads Directory (Keep 'system' folder for logos)
        uploads_dir = settings.UPLOAD_DIR
        if os.path.exists(uploads_dir):
            for item in os.listdir(uploads_dir):
                item_path = os.path.join(uploads_dir, item)
                if item == 'system':
                    continue 
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)

        await db.commit()
        return {"message": "System reset successfully"}

    except Exception as e:
        await db.rollback()
        print(f"Reset error: {e}")
        raise HTTPException(status_code=500, detail=f"System reset failed: {str(e)}")
