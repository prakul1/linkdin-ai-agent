"""Upload endpoints: file upload (PDF/image) + link ingestion."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import Optional
from io import BytesIO
from app.db.session import get_db
from app.models.attachment import Attachment, AttachmentType
from app.models.post import Post
from app.models.user import User
from app.schemas.upload import LinkUploadRequest, FileUploadResponse
from app.services.ingestion_service import IngestionService
from app.services.storage_service import StorageService
from app.api.deps import get_current_user
from app.utils.file_utils import detect_file_kind, validate_file_size
from app.utils.logger import logger
router = APIRouter(prefix="/api/uploads", tags=["uploads"])
def _build_response(att):
    text = att.extracted_text or ""
    return FileUploadResponse(
        id=att.id,
        file_type=att.file_type,
        original_filename=att.original_filename,
        url=att.url,
        file_size=att.file_size,
        extracted_text_preview=text[:200],
        extracted_text_length=len(text),
        created_at=att.created_at,
    )
def _verify_post_owner(db, post_id, user_id):
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == user_id).first()
    if not post:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")
    return post
@router.post("/file", response_model=FileUploadResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    post_id: Optional[int] = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    kind = detect_file_kind(file.filename or "", file.content_type)
    if not kind:
        raise HTTPException(status_code=400, detail="Unsupported file type. Allowed: PDF, JPG, PNG, WEBP.")
    contents = await file.read()
    if not validate_file_size(len(contents)):
        raise HTTPException(status_code=413, detail=f"File too large.")
    storage = StorageService()
    saved_path, size = storage.save_upload(BytesIO(contents), file.filename or "upload")
    ingestion = IngestionService()
    try:
        if kind == "pdf":
            extracted = ingestion.extract_pdf(saved_path)
            file_type = AttachmentType.PDF
        else:
            extracted = ingestion.extract_image(saved_path)
            file_type = AttachmentType.IMAGE
    except ValueError as e:
        storage.delete_file(saved_path)
        raise HTTPException(status_code=422, detail=str(e))
    if post_id is None:
        storage.delete_file(saved_path)
        raise HTTPException(
            status_code=400,
            detail="post_id is required. Generate a draft first, then upload attachments to it.",
        )
    _verify_post_owner(db, post_id, user.id)
    attachment = Attachment(
        post_id=post_id,
        file_type=file_type,
        file_path=saved_path,
        file_size=size,
        original_filename=file.filename,
        extracted_text=extracted,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    logger.info(f"Attachment {attachment.id} created (type={file_type})")
    return _build_response(attachment)
@router.post("/link", response_model=FileUploadResponse, status_code=201)
def upload_link(
    payload: LinkUploadRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.post_id is None:
        raise HTTPException(status_code=400, detail="post_id is required.")
    post = _verify_post_owner(db, payload.post_id, user.id)
    ingestion = IngestionService()
    try:
        extracted = ingestion.extract_link(str(payload.url))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    attachment = Attachment(
        post_id=post.id,
        file_type=AttachmentType.LINK,
        url=str(payload.url),
        extracted_text=extracted,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    logger.info(f"Link attachment {attachment.id} created for post {post.id}")
    return _build_response(attachment)
@router.delete("/{attachment_id}", status_code=204)
def delete_attachment(
    attachment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    att = (
        db.query(Attachment)
        .join(Post, Attachment.post_id == Post.id)
        .filter(Attachment.id == attachment_id, Post.user_id == user.id)
        .first()
    )
    if not att:
        raise HTTPException(status_code=404, detail="Attachment not found")
    if att.file_path:
        StorageService().delete_file(att.file_path)
    db.delete(att)
    db.commit()
    return None