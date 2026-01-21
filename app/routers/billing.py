from typing import List
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from .. import models
from ..schemas import InvoiceCreate, InvoiceRead, InvoiceUpdate

from app.utils.auth_utils import get_current_user 

router = APIRouter()

allowed_statuses = {"pending", "paid", "cancelled", "overdue"}

@router.post("/invoices", response_model=InvoiceRead)
async def create_invoice(invoice_in: InvoiceCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    if invoice_in.total_amount <= 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "message": "total_amount must be greater than 0"}
        )

    if invoice_in.status is not None:
        if invoice_in.status not in allowed_statuses:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "Invalid invoice status"}
            )

    client_exists = await db.execute(
        select(models.Client.id).where(models.Client.id == invoice_in.client_id)
    )
    if not client_exists.scalar_one_or_none():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "message": "Invalid client_id"}
        )
    
    invoice = models.Invoice(**invoice_in.model_dump())

    try:
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)
        return invoice
    except Exception as e:
        await db.rollback()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={ "success": False, "message": "Unexpected server error while creating invoice"})

@router.get("/invoices", response_model=List[InvoiceRead])
async def list_invoices(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        result = await db.execute(select(models.Invoice))
        return result.scalars().all()
    except Exception:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={ "success": False, "message": "Failed to fetch invoices"})
    

@router.get("/invoices/{invoice_id}", response_model=InvoiceRead)
async def get_invoice_by_id(invoice_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        result = await db.execute(select(models.Invoice).where(models.Invoice.id == invoice_id))
        invoice = result.scalar_one_or_none()

        if not invoice:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={ "success": False, "message": "Invoice not found"})

        return invoice

    except Exception:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={ "success": False, "message": "Failed to fetch invoice" })

    
@router.put("/invoices/{invoice_id}", response_model=InvoiceRead)
async def update_invoice( invoice_id: int, invoice_in: InvoiceUpdate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):

    result = await db.execute(select(models.Invoice).where(models.Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": "Invoice not found" })
    
    if invoice_in.total_amount is not None and invoice_in.total_amount <= 0:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={ "success": False, "message": "total_amount must be greater than 0"})

    if invoice_in.status is not None:
        if invoice_in.status not in allowed_statuses:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={ "success": False, "message": "Invalid invoice status"})
       
    update_data = invoice_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)
        
    try:
        await db.commit()
        await db.refresh(invoice)
        return invoice

    except Exception:
        await db.rollback()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "Unexpected server error while updating invoice" })

@router.delete("/invoices/{invoice_id}")
async def delete_invoice( invoice_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):

    result = await db.execute(select(models.Invoice).where(models.Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={ "success": False, "message": "Invoice not found" })

    try:
        await db.delete(invoice)
        await db.commit()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "message": "Invoice deleted successfully"}
        )

    except Exception:
        await db.rollback()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={ "success": False, "message": "Unexpected server error while deleting invoice"})
