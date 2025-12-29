from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.log_config import get_logger

logger = get_logger("appointment-utils")

async def validate_client_provider(
    db: AsyncSession,
    client_id: int | None = None,
    provider_id: int | None = None,
):
    logger.warning(f"appointment utils... client_id :{client_id}, provider_id: {provider_id}")
    if client_id is not None:
        logger.info(f"Fetching client, client_id={client_id}")
        client = await db.get(models.Client, client_id)
        if not client:
            logger.warning("Client not found",extra={"client_id": client_id})
            raise HTTPException(status_code=404, detail="Client not found")

    if provider_id is not None:
        logger.info(f"Fetching provider, provider_id={provider_id}")
        provider = await db.get(models.User, provider_id)
        if not provider:
            logger.warning("Provider not found",extra={"provider_id": provider_id})
            raise HTTPException(status_code=404, detail="Provider not found")


