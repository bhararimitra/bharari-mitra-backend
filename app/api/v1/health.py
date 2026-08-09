"""Health check endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timezone

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


@router.get("/health", response_model=HealthResponse)
async def health_check():
    from app.core.config import get_settings
    return HealthResponse(
        status="ok",
        version=get_settings().APP_VERSION,
        timestamp=datetime.now(timezone.utc),
    )
