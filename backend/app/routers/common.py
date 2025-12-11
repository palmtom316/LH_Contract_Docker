"""
Common Utility Router
1. Company Autocomplete Source
2. File Upload
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct, union
from typing import List
import os
import shutil
import uuid
from datetime import datetime

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.contract_upstream import ContractUpstream
from app.models.contract_downstream import ContractDownstream
from app.services.auth import get_current_active_user

router = APIRouter()

@router.get("/companies", response_model=List[str])
async def get_companies(
    query: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get unique company names from existing contracts for autocomplete.
    Scans:
    - ContractUpstream.party_a_name (甲方)
    - ContractDownstream.supplier_name (乙方/供应商)
    """
    # Create queries for both tables
    stmt_upstream = select(ContractUpstream.party_a_name).where(
        ContractUpstream.party_a_name.ilike(f"%{query}%")
    )
    stmt_downstream = select(ContractDownstream.party_b_name).where(
        ContractDownstream.party_b_name.ilike(f"%{query}%")
    )
    
    # Execute queries
    result_upstream = await db.execute(stmt_upstream)
    up_names = [r for r in result_upstream.scalars().all() if r]
    
    result_downstream = await db.execute(stmt_downstream)
    down_names = [r for r in result_downstream.scalars().all() if r]
    
    # Combine and de-duplicate
    all_names = sorted(list(set(up_names + down_names)))
    
    # Limit results for performance
    return all_names[:50]


@router.post("/upload", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload file (PDF, Images, Excel)
    Returns: {"filename": str, "url": str, "content_type": str}
    """
    # Validate extension
    ext = file.filename.split('.')[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")
    
    # Generate unique filename using UUID to avoid encoding issues
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    new_filename = f"{timestamp}_{unique_id}.{ext}"
    
    # Determine sub-folder based on extension
    sub_folder = "others"
    if ext in ['pdf']:
        sub_folder = "contracts"
    elif ext in ['jpg', 'jpeg', 'png']:
        sub_folder = "receipts"
    elif ext in ['xlsx', 'xls']:
        sub_folder = "docs"
        
    save_dir = os.path.join(settings.UPLOAD_DIR, sub_folder)
    os.makedirs(save_dir, exist_ok=True)
    
    file_path = os.path.join(save_dir, new_filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="文件保存失败")
        
    # Generate relative URL (assuming static mount at /uploads)
    relative_url = f"/uploads/{sub_folder}/{new_filename}"
    
    return {
        "filename": file.filename,
        "path": relative_url,
        "content_type": file.content_type
    }
