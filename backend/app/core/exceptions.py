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
    import traceback
    error_detail = f"{type(exc).__name__}: {str(exc)}"
    stack_trace = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    
    # Log to logger
    logger.error(f"Unhandled exception: {error_detail}")
    logger.error(f"Stack trace:\n{stack_trace}")
    
    # Also print to console explicitly
    print(f"\n{'='*80}")
    print(f"UNHANDLED EXCEPTION in {request.url.path}")
    print(f"{error_detail}")
    print(f"Stack trace:\n{stack_trace}")
    print(f"{'='*80}\n")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"服务器内部错误: {error_detail}", "trace": stack_trace.split('\n')[:10]}  # First 10 lines of trace
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
