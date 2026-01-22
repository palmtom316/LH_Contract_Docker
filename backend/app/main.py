"""
Safe Mode Main Application
Disabling all complex middleware to fix 'startlette.responses.Response' error.
"""
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
import os
import logging

from app.config import settings
from app.database import init_db, close_db, get_db
from app.init_data import init_data
from app.core.errors import AppException
from app.core.exceptions import (
    global_exception_handler, 
    sqlalchemy_exception_handler
)

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info(f"[START] Starting {settings.APP_NAME}")
    await init_db()
    
    # Initialize cache
    try:
        from app.core.cache import init_cache
        await init_cache()
    except Exception as e:
        logger.warning(f"Cache init failed: {e}")
    
    await init_data()
    
    # 数据库结构检查 - 检测缺失的表和列
    try:
        from app.core.db_check import run_startup_check
        from app.database import engine
        await run_startup_check(engine)
    except Exception as e:
        logger.warning(f"Database schema check failed: {e}")
    
    yield
    
    try:
        from app.core.cache import close_cache
        await close_cache()
    except:
        pass
    await close_db()

app = FastAPI(
    title="LH Contract Management",
    version="1.5.4",
    lifespan=lifespan,
    redirect_slashes=False,
    docs_url="/docs",
    openapi_url="/openapi.json"

)

# Exception Handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup rate limiting (optional - requires slowapi)
try:
    from app.core.rate_limit import setup_rate_limiting
    setup_rate_limiting(app)
except Exception as e:
    logger.warning(f"Rate limiting setup failed: {e}")
# Mount static files
try:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
except Exception as e:
    logger.error(f"Failed to mount uploads: {e}")

@app.get("/", tags=["Health"])
async def root():
    return {"status": "healthy", "version": settings.APP_VERSION}

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail if isinstance(exc.detail, dict) else {
            "error_code": exc.error_code.value,
            "message": exc.message,
            "detail": exc.detail
        }
    )

# Routers
from app.routers import auth, users, contracts_upstream, contracts_downstream, contract_management, expenses, common, dashboard, reports, audit, system

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(contracts_upstream.router, prefix="/api/v1/contracts/upstream", tags=["Upstream Contracts"])
app.include_router(contracts_downstream.router, prefix="/api/v1/contracts/downstream", tags=["Downstream Contracts"])
app.include_router(contract_management.router, prefix="/api/v1/contracts/management", tags=["Management Contracts"])
app.include_router(expenses.router, prefix="/api/v1/expenses", tags=["Expenses"])
app.include_router(common.router, prefix="/api/v1/common", tags=["Common"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit Logs"])
app.include_router(system.router, prefix="/api/v1/system", tags=["System Management"])

# New Router
from app.routers import zero_hour_labor
app.include_router(zero_hour_labor.router, prefix="/api/v1/zero-hour-labor", tags=["Zero Hour Labor"])

# Contract Search Router (查询机器人)
from app.routers import contract_search
app.include_router(contract_search.router, prefix="/api/v1/contracts", tags=["Contract Search"])

# Feishu Integration (V1.4)
from app.routers import feishu
app.include_router(feishu.router, prefix="/api/feishu", tags=["Feishu Integration"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
