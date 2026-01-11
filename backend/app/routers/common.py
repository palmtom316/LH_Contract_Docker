"""
Common Utility Router
1. Company Autocomplete Source
2. File Upload
Refactored to use standardized AppException
"""
from fastapi import APIRouter, Depends, status, UploadFile, File, Form
import logging
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
from app.models.contract_management import ContractManagement
from app.services.auth import get_current_active_user
from app.core.errors import ValidationError, DatabaseError

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
    # Create queries for all relevant tables
    # 1. Upstream Party A (Client) & Party B (If editable)
    stmt_up_a = select(ContractUpstream.party_a_name).where(
        ContractUpstream.party_a_name.ilike(f"%{query}%")
    )
    stmt_up_b = select(ContractUpstream.party_b_name).where(
        ContractUpstream.party_b_name.ilike(f"%{query}%")
    )
    
    # 2. Downstream Party A (Usually us, but maybe editable) & Party B (Supplier)
    stmt_down_a = select(ContractDownstream.party_a_name).where(
        ContractDownstream.party_a_name.ilike(f"%{query}%")
    )
    stmt_down_b = select(ContractDownstream.party_b_name).where(
        ContractDownstream.party_b_name.ilike(f"%{query}%")
    )
    
    # 3. Management Party A & B
    stmt_mgmt_a = select(ContractManagement.party_a_name).where(
        ContractManagement.party_a_name.ilike(f"%{query}%")
    )
    stmt_mgmt_b = select(ContractManagement.party_b_name).where(
        ContractManagement.party_b_name.ilike(f"%{query}%")
    )
    
    # Execute queries
    res_up_a = await db.execute(stmt_up_a)
    res_up_b = await db.execute(stmt_up_b)
    res_down_a = await db.execute(stmt_down_a)
    res_down_b = await db.execute(stmt_down_b)
    res_mgmt_a = await db.execute(stmt_mgmt_a)
    res_mgmt_b = await db.execute(stmt_mgmt_b)
    
    names = set()
    for r in res_up_a.scalars().all():
        if r: names.add(r)
    for r in res_up_b.scalars().all():
        if r: names.add(r)
    for r in res_down_a.scalars().all():
        if r: names.add(r)
    for r in res_down_b.scalars().all():
        if r: names.add(r)
    for r in res_mgmt_a.scalars().all():
        if r: names.add(r)
    for r in res_mgmt_b.scalars().all():
        if r: names.add(r)
    
    # Combine and de-duplicate
    all_names = sorted(list(names))
    
    # Limit results for performance
    return all_names[:50]


logger = logging.getLogger(__name__)

@router.post("/upload", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
    upload_dir: str = Form(default=None),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload file to MinIO storage.
    
    Args:
        file: The file to upload
        upload_dir: Not strictly used for folders in MinIO, but used for prefixing if needed.
                    Allowed: contracts, invoices, receipts, settlements, expenses, etc.
    
    Returns: 
        {
            "filename": str, 
            "path": str (presigned url or public url), 
            "key": str (object name),
            "content_type": str
        }
    """
    logger.info(f"[UPLOAD] Start: filename={file.filename}, content_type={file.content_type}, upload_dir={upload_dir}, user={current_user.username}")
    
    # 1. Validate extension
    ext = file.filename.split('.')[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise ValidationError(
            message="不支持的文件类型",
            field_errors={"file": f"不支持的文件类型: {ext}，支持的类型: {', '.join(settings.ALLOWED_EXTENSIONS)}"}
        )
    
    # 2. Generate Object Key
    # Format: {year}/{month}/{uuid}.{ext} to avoid flat folder limit issues
    now = datetime.now()
    unique_id = str(uuid.uuid4())
    object_name = f"{now.year}/{now.month:02d}/{unique_id}.{ext}"
    
    # If upload_dir provided, maybe prefix it? 
    # For now, let's keep all in one bucket but maybe prefix by type if helpful, 
    # but strictly following V1.5 plan, we just need a unique key.
    # Let's add the type as prefix for better organization: {type}/{year}/{month}/{uuid}.{ext}
    
    type_prefix = "others"
    allowed_dirs = ['contracts', 'invoices', 'receipts', 'settlements', 'expenses', 'docs']
    
    if upload_dir and upload_dir in allowed_dirs:
        type_prefix = upload_dir
    else:
        if ext in ['pdf']: type_prefix = "contracts"
        elif ext in ['jpg', 'jpeg', 'png']: type_prefix = "receipts"
        elif ext in ['xlsx', 'xls']: type_prefix = "docs"
        
    final_object_name = f"{type_prefix}/{object_name}"

    # 3. Upload to MinIO
    try:
        from app.core.minio import get_minio_client, ensure_bucket_exists
        
        client = get_minio_client()
        bucket_name = settings.MINIO_BUCKET_CONTRACTS
        
        # Ensure bucket exists
        ensure_bucket_exists(client, bucket_name)
        
        # Determine file size (files are spooled, need to check size)
        # file.file is a SpooledTemporaryFile
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        client.put_object(
            bucket_name,
            final_object_name,
            file.file,
            file_size,
            content_type=file.content_type
        )
        logger.info(f"[UPLOAD] Success: uploaded to {bucket_name}/{final_object_name}")
        
    except Exception as e:
        logger.error(f"[UPLOAD] MinIO upload failed: {e}")
        raise DatabaseError(message="文件上传失败", detail=str(e))

    # 4. Generate URL
    # For now, generate a presigned URL valid for 7 days (or less)
    # OR if public, just return the path.
    # Contract files are sensitive, so we should typically use presigned URLs or proxy.
    # For simplicity in list views (high traffic), usually we proxy or use long-lived presigned.
    # In this specific context, the Frontend expects a "path" which it might use to preview.
    # Verification: The existing frontend uses `getFileUrl` utils.
    
    # Let's return a special path that the frontend can interpret or use directly if proxy is setup.
    # Returning the key is critical for the DB update.
    
    # We will return the object key as 'path' essentially, or a path that our backend proxy understands.
    # V1.5 Design: MinIO key is the source of truth.
    
    return {
        "filename": file.filename,
        "path": final_object_name,  # Frontend might show this or we return a view URL?
        "key": final_object_name,   # Explicit key
        "url": f"/api/v1/common/files/{final_object_name}", # Hypothetical proxy endpoint or direct minio link
        "content_type": file.content_type
    }


