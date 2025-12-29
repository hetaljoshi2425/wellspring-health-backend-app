from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import select, or_, func, and_

from ..database import get_db
from .. import models
from ..schemas import ClientCreate, ClientRead, ClientUpdate
from app.utils.auth_utils import get_current_user 

router = APIRouter()

@router.post("/", response_model=ClientRead)
async def create_client(client_in: ClientCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    if client_in.email or client_in.phone:
        stmt = select(models.Client).where(
            or_(
                models.Client.email == client_in.email if client_in.email else False,
                models.Client.phone == client_in.phone if client_in.phone else False,
            )
        )
        result = await db.execute(stmt)
        if result.scalars().first():
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Client with this email or phone already exists."})
    client = models.Client(**client_in.model_dump())
    db.add(client)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return JSONResponse(
            status_code=409,
            content={"success": False, "message": "Duplicate email or phone number."})
    return client

@router.get("/", response_model=List[ClientRead])
async def list_clients(
    search: Optional[str] = Query(None, description="Search by name or email"),
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        stmt = select(models.Client)

        if search:
            search_term = f"%{search.lower()}%"
            full_name = (models.Client.first_name + " " + models.Client.last_name)

            stmt = stmt.where(
                or_(
                    func.lower(models.Client.first_name).ilike(search_term),
                    func.lower(models.Client.last_name).ilike(search_term),
                    func.lower(full_name).ilike(search_term),
                    func.lower(models.Client.email).ilike(search_term),
                )
            )

        # Latest client first
        stmt = stmt.order_by(models.Client.created_at.desc())
        if page is not None and page_size is not None:
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)


        result = await db.execute(stmt)
        clients = result.scalars().all()

        return clients

    except SQLAlchemyError as db_err:
        print("Database error while listing clients")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "Failed to fetch clients from database"})

    except Exception as exc:
        print("Unexpected error while listing clients")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "Unexpected server error"})


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(client_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(select(models.Client).where(models.Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        return JSONResponse(status_code=404, content={"success": False, "message": "Client not found"})
    return client


@router.patch("/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: int,
    client_in: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Fetch client
    result = await db.execute(
        select(models.Client).where(models.Client.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"success": False, "message": "Client not found"})

    # Duplicate check (exclude current client)
    if client_in.email or client_in.phone:
        stmt = select(models.Client).where(
            and_(
                models.Client.id != client_id,  
                or_(
                    models.Client.email == client_in.email if client_in.email else False,
                    models.Client.phone == client_in.phone if client_in.phone else False,
                ),
            )
        )

        result = await db.execute(stmt)
        if result.scalars().first():
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": "Client with this email or phone already exists."})

    # Update only changed field
    update_data = client_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT, content={"success": False, "message": "Duplicate email or phone number."})

    await db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
async def delete_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        result = await db.execute(
            select(models.Client).where(models.Client.id == client_id)
        )
        client = result.scalar_one_or_none()

        if client is None:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": "Client not found"})

        await db.delete(client)
        await db.commit()
        
        return {
            "success": True,
            "message": "Client deleted successfully",
            "client_id": client_id,
        }

    except Exception as e:
        await db.rollback()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": f"Unexpected error: {str(e)}"})