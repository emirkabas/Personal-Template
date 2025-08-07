"""
Health check endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import time
from typing import Dict, Any

from app.database.session import get_db

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "service": "apartment-scraper-api"
    }

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Detailed health check including database connectivity."""
    health_status = {
        "status": "healthy",
        "timestamp": int(time.time()),
        "service": "apartment-scraper-api",
        "checks": {}
    }
    
    # Check database connection
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    # Add more checks here as needed
    # For example: Redis, external APIs, disk space, etc.
    
    return health_status

@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)) -> Dict[str, str]:
    """Kubernetes-style readiness probe."""
    try:
        # Check if the application is ready to serve requests
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not ready"}

@router.get("/health/live")
async def liveness_check() -> Dict[str, str]:
    """Kubernetes-style liveness probe."""
    # Basic liveness check - just confirm the process is running
    return {"status": "alive"}