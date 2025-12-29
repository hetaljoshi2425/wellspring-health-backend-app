from datetime import datetime, timezone
from fastapi import status
from fastapi.responses import JSONResponse
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
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,content={"success": False,"message": "Client not found"})

    if provider_id is not None:
        provider = await db.get(models.User, provider_id)
        if not provider:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False,"message": "Provider not found"})


