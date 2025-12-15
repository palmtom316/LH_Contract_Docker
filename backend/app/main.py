"""
LH Contract Management System - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager
import os
import logging

from app.config import settings
from app.database import init_db, close_db
from app.init_data import init_data
from app.core.logging_config import setup_logging
from app.core.exceptions import (
    global_exception_handler, 
    sqlalchemy_exception_handler, 
    validation_exception_handler
)

# Setup Logging
setup_logging()
logger = logging.getLogger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    logger.info("✅ Database tables initialized")
    await init_data()
    
    yield
    
    # Shutdown
    await close_db()
    logger.info("👋 Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="蓝海电气合同管理系统 - Contract Management System for Lanhai Electrical Engineering",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    redirect_slashes=False  # Prevent 307 redirects that lose Authorization header
)

# Exception Handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
# We can override validation handler if we want custom format, strict JSON
# app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Configure CORS - Use whitelist from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Use configured whitelist
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

# Mount static files for uploads
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - health check"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "status": "healthy"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for container orchestration"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/api/v1/info", tags=["System"])
async def system_info():
    """Get system information"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }


# Import and include routers
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
