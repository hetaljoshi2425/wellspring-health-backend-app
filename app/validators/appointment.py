from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import models


async def validate_client_provider(
    db: AsyncSession,
    client_id: int | None = None,
    provider_id: int | None = None,
):
    if client_id is not None:
        client = await db.get(models.Client, client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

    if provider_id is not None:
        provider = await db.get(models.User, provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")


