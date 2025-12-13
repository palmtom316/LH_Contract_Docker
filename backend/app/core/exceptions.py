from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger("app.core.exceptions")

async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler for unhandled exceptions.
    Logs the full stack trace and returns a generic 500 error.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"服务器内部错误: {str(exc)}"} if True else {"detail": "服务器内部错误"} # Show details in dev/beta
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Handle Database errors gracefully.
    """
    logger.error(f"Database error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "数据库操作失败"}
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors.
    """
    # Simply use FastAPI's default logic but maybe log it if needed
    # For now, return default JSON response structure
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body}
    )
