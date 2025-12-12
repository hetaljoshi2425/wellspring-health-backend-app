from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from reportlab.pdfgen import canvas

from ..database import get_db
from .. import models

router = APIRouter()

def _pdf_response(buffer: BytesIO, filename: str) -> StreamingResponse:
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )

@router.get("/superbill/{invoice_id}")
async def generate_superbill(invoice_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Invoice).where(models.Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    result = await db.execute(select(models.Client).where(models.Client.id == invoice.client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    result = await db.execute(
        select(models.ProgressNote)
        .where(models.ProgressNote.client_id == client.id)
        .order_by(models.ProgressNote.created_at.desc())
    )
    latest_note = result.scalars().first()

    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setTitle("Superbill")

    y = 800
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Wellspring Family & Community Institute")
    y -= 20
    p.setFont("Helvetica", 12)
    p.drawString(50, y, "Superbill")
    y -= 30

    p.drawString(50, y, f"Client: {client.first_name} {client.last_name}")
    y -= 20
    p.drawString(50, y, f"Invoice ID: {invoice.id}")
    y -= 20
    p.drawString(50, y, f"Date: {invoice.created_at.strftime('%Y-%m-%d')}")
    y -= 20
    p.drawString(50, y, f"Total Amount: ${invoice.total_amount:0.2f}")
    y -= 30

    if latest_note and latest_note.dsm5_code:
        p.drawString(50, y, f"DSM/ICD Code: {latest_note.dsm5_code}")
        y -= 20
        p.drawString(50, y, "Diagnosis based on latest clinical documentation.")
        y -= 30

    p.drawString(50, y, "This superbill is provided for insurance reimbursement purposes.")
    p.showPage()
    p.save()
    return _pdf_response(buffer, f"superbill_{invoice.id}.pdf")

@router.get("/consent/{client_id}")
async def generate_consent_form(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Client).where(models.Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setTitle("Consent for Treatment")

    y = 800
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Wellspring Family & Community Institute")
    y -= 20
    p.setFont("Helvetica", 12)
    p.drawString(50, y, "Consent for Treatment")
    y -= 40

    p.drawString(50, y, f"Client Name: {client.first_name} {client.last_name}")
    y -= 40

    lines = [
        "I hereby consent to receive mental and behavioral health services from",
        "Wellspring Family & Community Institute and its affiliated providers.",
        "",
        "I understand that I may withdraw this consent in writing at any time,",
        "except to the extent that action has already been taken in reliance on it.",
        "",
        "Client / Legal Guardian Signature: _____________________________",
        "",
        "Date: _____________________________",
    ]
    for line in lines:
        p.drawString(50, y, line)
        y -= 20

    p.showPage()
    p.save()
    return _pdf_response(buffer, f"consent_{client.id}.pdf")

@router.get("/intake/{client_id}")
async def generate_intake_packet(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Client).where(models.Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setTitle("Intake Packet")

    y = 800
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Wellspring Family & Community Institute")
    y -= 20
    p.setFont("Helvetica", 12)
    p.drawString(50, y, "Client Intake Packet")
    y -= 40

    p.drawString(50, y, f"Client Name: {client.first_name} {client.last_name}")
    y -= 20
    if client.date_of_birth:
        p.drawString(50, y, f"DOB: {client.date_of_birth.strftime('%Y-%m-%d')}")
        y -= 20
    if client.phone:
        p.drawString(50, y, f"Phone: {client.phone}")
        y -= 20
    if client.email:
        p.drawString(50, y, f"Email: {client.email}")
        y -= 20
    if client.address:
        p.drawString(50, y, f"Address: {client.address}")
        y -= 20

    y -= 40
    p.drawString(50, y, "Presenting Problem (completed by clinician):")
    y -= 60
    p.line(50, y, 550, y)
    y -= 40
    p.line(50, y, 550, y)

    y -= 60
    p.drawString(50, y, "Insurance Information (completed by front desk/billing):")
    y -= 60
    p.line(50, y, 550, y)
    y -= 40
    p.line(50, y, 550, y)

    p.showPage()
    p.save()
    return _pdf_response(buffer, f"intake_{client.id}.pdf")

@router.get("/payment-consent/{client_id}")
async def generate_payment_consent(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Client).where(models.Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setTitle("Credit/Debit Card Payment Consent")

    y = 800
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Wellspring Family & Community Institute")
    y -= 20
    p.setFont("Helvetica", 12)
    p.drawString(50, y, "Credit / Debit Card Payment Consent")
    y -= 40

    p.drawString(50, y, f"Client Name: {client.first_name} {client.last_name}")
    y -= 40

    lines = [
        "I authorize Wellspring Family & Community Institute to charge my credit/debit card",
        "for services rendered, including copayments, coinsurance, deductibles, and any",
        "fees not covered by my insurance plan.",
        "",
        "I understand that this authorization will remain in effect until I cancel it in writing.",
        "",
        "Type of Card: ____________________________",
        "Name on Card: ____________________________",
        "Last 4 Digits of Card: ____  Expiration: ____ / ____",
        "",
        "Client / Cardholder Signature: _____________________________",
        "",
        "Date: _____________________________",
    ]
    for line in lines:
        p.drawString(50, y, line)
        y -= 20

    p.showPage()
    p.save()
    return _pdf_response(buffer, f"payment_consent_{client.id}.pdf")

@router.get("/telehealth-consent/{client_id}")
async def generate_telehealth_consent(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Client).where(models.Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setTitle("Telehealth Treatment Consent")

    y = 800
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Wellspring Family & Community Institute")
    y -= 20
    p.setFont("Helvetica", 12)
    p.drawString(50, y, "Telehealth Treatment Consent")
    y -= 40

    p.drawString(50, y, f"Client Name: {client.first_name} {client.last_name}")
    y -= 40

    lines = [
        "I understand that telehealth services involve the use of electronic",
        "communications to enable mental health providers at a different location",
        "to provide services to me.",
        "",
        "I understand the potential risks and benefits of telehealth and the",
        "alternatives to receiving services via telehealth.",
        "",
        "I consent to receive mental and behavioral health services via telehealth",
        "from Wellspring Family & Community Institute.",
        "",
        "Client / Legal Guardian Signature: _____________________________",
        "",
        "Date: _____________________________",
    ]
    for line in lines:
        p.drawString(50, y, line)
        y -= 20

    p.showPage()
    p.save()
    return _pdf_response(buffer, f"telehealth_consent_{client.id}.pdf")
