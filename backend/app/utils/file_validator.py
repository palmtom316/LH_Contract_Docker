"""
File Upload Validation Utilities
Enhanced security validation for file uploads
"""
from fastapi import UploadFile
from typing import List, Optional
import magic
import os
import re
from pathlib import Path
import logging

from app.config import settings
from app.core.errors import (
    FileUploadError,
    ResourceNotFoundError,
    ErrorCode,
)

logger = logging.getLogger(__name__)

# MIME type mapping for allowed file types
ALLOWED_MIME_TYPES = {
    'pdf': ['application/pdf'],
    'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
    'xls': ['application/vnd.ms-excel'],
    'doc': ['application/msword'],
    'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    'jpg': ['image/jpeg'],
    'jpeg': ['image/jpeg'],
    'png': ['image/png'],
}


def secure_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal attacks
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Remove or replace dangerous characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    
    # Replace multiple spaces/dots with single ones
    filename = re.sub(r'[\s.]+', '.', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    return filename


async def validate_file_upload(
    file: UploadFile,
    allowed_extensions: Optional[List[str]] = None,
    max_size: Optional[int] = None
) -> str:
    """
    Comprehensive file upload validation
    
    Args:
        file: Uploaded file object
        allowed_extensions: List of allowed file extensions (default from settings)
        max_size: Maximum file size in bytes (default from settings)
        
    Returns:
        Sanitized filename
        
    Raises:
        FileUploadError: If validation fails
    """
    if allowed_extensions is None:
        allowed_extensions = settings.ALLOWED_EXTENSIONS

    if max_size is None:
        max_size = settings.MAX_FILE_SIZE

    # 1. Check if file exists
    if not file or not file.filename:
        raise FileUploadError(message="未选择文件")

    # 2. Sanitize filename
    safe_name = secure_filename(file.filename)
    if not safe_name:
        raise FileUploadError(message="无效的文件名")

    # 3. Check file extension
    file_ext = Path(safe_name).suffix.lower().lstrip('.')
    if file_ext not in allowed_extensions:
        raise FileUploadError(
            message="不支持的文件类型",
            detail=f"允许的类型: {', '.join(allowed_extensions)}",
            error_code=ErrorCode.FILE_TYPE_NOT_ALLOWED,
        )

    # 4. Read file content for size and type validation
    file_content = await file.read()
    file_size = len(file_content)

    # Reset file pointer
    await file.seek(0)

    # 5. Check file size
    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise FileUploadError(
            message="文件大小超过限制",
            detail=f"最大 {max_size_mb:.1f}MB",
            error_code=ErrorCode.FILE_TOO_LARGE,
        )

    # 6. Validate file type using magic numbers (more secure than extension)
    try:
        file_type = magic.from_buffer(file_content[:2048], mime=True)

        # Check if detected MIME type matches allowed types for this extension
        allowed_mimes = ALLOWED_MIME_TYPES.get(file_ext, [])
        if allowed_mimes and file_type not in allowed_mimes:
            logger.warning(
                f"MIME type mismatch: extension={file_ext}, "
                f"detected={file_type}, allowed={allowed_mimes}"
            )
            raise FileUploadError(
                message="文件内容与扩展名不匹配",
                detail=f"检测到的类型: {file_type}",
                error_code=ErrorCode.FILE_TYPE_NOT_ALLOWED,
            )

        logger.info(f"File validation passed: {safe_name} ({file_type}, {file_size} bytes)")

    except FileUploadError:
        raise
    except Exception as e:
        logger.error(f"File type detection error: {e}")
        # If magic detection fails, we still allow the file if extension is valid
        logger.warning(f"Could not detect MIME type for {safe_name}, allowing based on extension")

    return safe_name


def validate_file_size_sync(file_path: str, max_size: Optional[int] = None) -> bool:
    """
    Synchronous file size validation for already uploaded files

    Args:
        file_path: Path to the file
        max_size: Maximum file size in bytes

    Returns:
        True if valid, raises exception otherwise
    """
    if max_size is None:
        max_size = settings.MAX_FILE_SIZE

    if not os.path.exists(file_path):
        raise ResourceNotFoundError(resource_type="文件", error_code=ErrorCode.FILE_NOT_FOUND)

    file_size = os.path.getsize(file_path)
    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise FileUploadError(
            message="文件大小超过限制",
            detail=f"最大 {max_size_mb:.1f}MB",
            error_code=ErrorCode.FILE_TOO_LARGE,
        )

    return True
