from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

import json, uuid
from typing import List, Optional
import os

from ..database import get_db
from .. import models
from ..schemas import DocumentCreate, DocumentRead
from app.utils.auth_utils import get_current_user
router = APIRouter()

@router.post("/", response_model=DocumentRead)
async def create_document(client_id: int = Form(...), document_type: str = Form(...), title: str = Form(...), file: UploadFile = File(...),  db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        doc_in = DocumentCreate(
            client_id=client_id,
            document_type=document_type,
            title=title,
        )
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False,"message": "Invalid document data"})

    if not file.filename:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False,"message": "File is required"})

    upload_dir = "uploads/documents"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = f"{upload_dir}/{uuid.uuid4()}_{file.filename}"

    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        print("File save failed")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "Failed to save file"})

    try:
        doc = models.Document(
            **doc_in.model_dump(),
            file_path=file_path,
            uploaded_by_user_id=current_user.id
        )

        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        return DocumentRead(
            id=doc.id,
            client_id=doc.client_id,
            document_type=doc.document_type,
            title=doc.title,
            file_path=doc.file_path,
            uploaded_at=doc.uploaded_at,
            uploaded_by_user=current_user.user_name,
        )

    except Exception as e:
        await db.rollback()

        if os.path.exists(file_path):
            os.remove(file_path)

        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": "Failed to create document"})

@router.get("/client/{client_id}", response_model=List[DocumentRead])
async def list_documents(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    search: Optional[str] = Query(None, description="Search document by title"),
):
    query = (
        select(
            models.Document,
            models.User.user_name.label("uploaded_by_user_user_name")
        )
        .outerjoin(
            models.User,
            models.User.id == models.Document.uploaded_by_user_id
        )
        .where(models.Document.client_id == client_id)
        .order_by(models.Document.uploaded_at.desc())
    )

    if search:
        query = query.where(
            func.lower(models.Document.title).ilike(f"%{search.lower()}%")
        )

    result = await db.execute(query)

    return [
        DocumentRead(
            id=doc.id,
            client_id=doc.client_id,
            document_type=doc.document_type,
            title=doc.title,
            file_path=doc.file_path,
            uploaded_at=doc.uploaded_at,
            uploaded_by_user=user_name,
        )
        for doc, user_name in result.all()
    ]


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(models.Document).where(models.Document.id == document_id)
    )
    document = result.scalars().first()

    if not document:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": "Document not found"})

    # Delete existing files
    if document.file_path and os.path.exists(document.file_path):
        os.remove(document.file_path)

    await db.delete(document)
    await db.commit()
    return {
        "success": True,
        "message": "Document deleted successfully",
        "document_id": document_id
    }
    
    
@router.get("/download/{document_id}")
async def download_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(
        select(models.Document).where(models.Document.id == document_id)
    )
    document = result.scalars().first()

    if not document:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": "Document not found"})

    if not document.file_path or not os.path.exists(document.file_path):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": "Document file not found"})

    return FileResponse(
        path=document.file_path,
        filename=document.title,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{document.title}"'
        },
    )
