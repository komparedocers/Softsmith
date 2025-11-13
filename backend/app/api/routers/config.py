"""
Configuration API router - endpoints for managing system configuration.
"""
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import get_config, reload_config
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/config", tags=["config"])


class ConfigResponse(BaseModel):
    """Configuration response model."""
    llm_mode: str
    providers: dict
    app_settings: dict


@router.get("", response_model=ConfigResponse)
async def get_configuration():
    """Get current system configuration."""
    config = get_config()

    return ConfigResponse(
        llm_mode=config.llm.mode,
        providers={
            name: {
                "enabled": provider.enabled,
                "model": provider.model,
            }
            for name, provider in config.llm.providers.items()
        },
        app_settings={
            "max_retries": config.app.max_retries,
            "max_concurrent_projects": config.app.max_concurrent_projects,
            "max_fix_attempts": config.app.max_fix_attempts,
        }
    )


@router.post("/reload")
async def reload_configuration():
    """Reload configuration from file."""
    reload_config()
    logger.info("Configuration reloaded")
    return {"message": "Configuration reloaded successfully"}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "software-maker-api"
    }
