"""
Common Utility Router
1. Company Autocomplete Source
2. File Upload
Refactored to use standardized AppException
"""
from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException, Request
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct, union
from typing import List, Optional
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
from app.core.errors import ValidationError, DatabaseError, PermissionDeniedError
from app.core.validators import FileValidators
from app.services.file_authorization import user_can_access_file_path
from app.utils.file_validator import validate_file_upload

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
    fuzzy = f"%{query}%"
    companies_subquery = union(
        select(ContractUpstream.party_a_name.label("name")).where(ContractUpstream.party_a_name.ilike(fuzzy)),
        select(ContractUpstream.party_b_name.label("name")).where(ContractUpstream.party_b_name.ilike(fuzzy)),
        select(ContractDownstream.party_a_name.label("name")).where(ContractDownstream.party_a_name.ilike(fuzzy)),
        select(ContractDownstream.party_b_name.label("name")).where(ContractDownstream.party_b_name.ilike(fuzzy)),
        select(ContractManagement.party_a_name.label("name")).where(ContractManagement.party_a_name.ilike(fuzzy)),
        select(ContractManagement.party_b_name.label("name")).where(ContractManagement.party_b_name.ilike(fuzzy)),
    ).subquery()

    stmt = (
        select(distinct(companies_subquery.c.name))
        .where(companies_subquery.c.name.is_not(None), companies_subquery.c.name != "")
        .order_by(companies_subquery.c.name)
        .limit(50)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


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

    # 1. Validate filename, extension, MIME signature, and size
    safe_name = await validate_file_upload(file)
    ext = safe_name.rsplit('.', 1)[-1].lower()
    
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

        if file_size > settings.MAX_FILE_SIZE:
            raise ValidationError(
                message="文件过大",
                field_errors={"file": f"文件大小超过限制 {settings.MAX_FILE_SIZE // (1024 * 1024)}MB"}
            )
        
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


from fastapi.responses import StreamingResponse, FileResponse
from app.core.minio import get_minio_client
from app.services.auth import get_current_user, get_user_from_token
import mimetypes

@router.get("/files/{path:path}")
async def get_file(
    path: str,
    request: Request,
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get file from MinIO or local storage.
    Supports token in Authorization header or query parameter.
    """
    current_user = None
    # Validate path to prevent traversal
    try:
        safe_path = FileValidators.validate_file_path(path)
    except ValueError:
        raise ValidationError(
            message="非法的文件路径",
            field_errors={"path": "文件路径非法"}
        )

    # Query token transport is intentionally forbidden to avoid token leakage
    if token:
        raise ValidationError(
            message="不允许使用查询参数令牌",
            field_errors={"token": "请使用 Authorization 头部"}
        )
            
    # If still no user, try to get from Authorization header manually
    if not current_user:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            bearer_token = auth_header.replace("Bearer ", "")
            current_user = await get_user_from_token(bearer_token, db)
    
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not await user_can_access_file_path(safe_path, db, current_user):
        raise PermissionDeniedError(
            message="无权访问该文件",
            detail="该文件未授权给当前用户"
        )

    logger.info(f"[FILE_GET] Request: path={safe_path}, user={current_user.username}")
    
    # 1. Try MinIO first
    try:
        client = get_minio_client()
        bucket_name = settings.MINIO_BUCKET_CONTRACTS
        
        # Check if object exists
        try:
            stat = client.stat_object(bucket_name, safe_path)
            
            # Get data stream
            response = client.get_object(bucket_name, safe_path)
            
            # Guess mime type
            mime_type, _ = mimetypes.guess_type(safe_path)
            if not mime_type:
                mime_type = "application/octet-stream"
                
            # Use a generator to stream data in efficient chunks (1MB)
            def data_generator():
                try:
                    # Stream in 1MB chunks
                    for chunk in response.stream(1024 * 1024):
                        yield chunk
                finally:
                    response.close()
                    response.release_conn()
                    
            return StreamingResponse(
                data_generator(),
                media_type=mime_type,
                headers={
                    "Content-Length": str(stat.size),
                    "Content-Disposition": f"inline; filename={os.path.basename(safe_path)}",
                    "Accept-Ranges": "bytes"
                }
            )
        except Exception as e:
            # Not found in MinIO or other error, fallback to local
            logger.debug(f"[FILE_GET] MinIO fallback: {e}")
            pass
            
    except Exception as e:
        logger.error(f"[FILE_GET] MinIO error: {e}")
        # Continue to local fallback
    
    # 2. Local fallback
    local_path = os.path.normpath(os.path.join(settings.UPLOAD_DIR, safe_path))
    local_real_path = os.path.realpath(local_path)
    uploads_root_real = os.path.realpath(settings.UPLOAD_DIR)
    if local_real_path != uploads_root_real and not local_real_path.startswith(uploads_root_real + os.sep):
        raise ValidationError(
            message="非法的文件路径",
            field_errors={"path": "文件路径非法"}
        )
    if os.path.exists(local_real_path) and os.path.isfile(local_real_path):
        return FileResponse(local_real_path)
    
    # 3. Not found anywhere
    logger.warning(f"[FILE_GET] Not Found: {safe_path}")
    raise ValidationError(
        message="文件不存在",
        field_errors={"path": f"文件不存在: {path}"}
    )


