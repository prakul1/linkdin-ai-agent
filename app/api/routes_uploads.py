"""Upload endpoints — Phase 9.5: media upload + download."""
import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from fastapi.responses import FileResponse
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
MAX_MEDIA_PER_POST = 3
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
# ============== EXISTING: CONTEXT UPLOAD (PDF/Image with OCR) ==============
@router.post(
    "/file",
    response_model=FileUploadResponse,
    status_code=201,
    summary="Upload PDF or image as CONTEXT (text extracted for LLM)",
)
async def upload_file(
    file: UploadFile = File(...),
    post_id: Optional[int] = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """For PDFs and images used as LLM reference (text extracted)."""
    kind = detect_file_kind(file.filename or "", file.content_type)
    if kind not in ("pdf", "image"):
        raise HTTPException(status_code=400,
            detail="For context, upload a PDF or image. For media to post, use /api/uploads/media")
    contents = await file.read()
    if not validate_file_size(len(contents)):
        raise HTTPException(status_code=413, detail="File too large")
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
        raise HTTPException(status_code=400,
            detail="post_id required. Generate a draft first.")
    _verify_post_owner(db, post_id, user.id)
    attachment = Attachment(
        post_id=post_id,
        file_type=file_type,
        file_path=saved_path,
        file_size=size,
        original_filename=file.filename,
        mime_type=file.content_type,
        extracted_text=extracted,
        is_media=False,   # Context-only
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return _build_response(attachment)
# ============== NEW PHASE 9.5: MEDIA UPLOAD (goes WITH the post) ==============
@router.post(
    "/media",
    response_model=FileUploadResponse,
    status_code=201,
    summary="Upload an image or video to be POSTED WITH the content",
)
async def upload_media(
    file: UploadFile = File(...),
    post_id: int = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Phase 9.5: Image/video that will be PUBLISHED to LinkedIn with the post text.
    
    - Max 3 media per post
    - Images: JPG/PNG/WEBP (uses MAX_UPLOAD_SIZE_MB limit)
    - Videos: MP4/MOV (max 30MB)
    """
    post = _verify_post_owner(db, post_id, user.id)
    # Check media count limit
    existing_media = (
        db.query(Attachment)
        .filter(Attachment.post_id == post_id, Attachment.is_media == True)
        .count()
    )
    if existing_media >= MAX_MEDIA_PER_POST:
        raise HTTPException(
            status_code=400,
            detail=f"Max {MAX_MEDIA_PER_POST} media attachments per post. "
                   f"Delete an existing one first.",
        )
    kind = detect_file_kind(file.filename or "", file.content_type)
    if kind not in ("image", "video"):
        raise HTTPException(
            status_code=400,
            detail="Only images (JPG/PNG/WEBP) or videos (MP4/MOV) allowed for media posts.",
        )
    contents = await file.read()
    if not validate_file_size(len(contents), kind=kind):
        max_mb = 30 if kind == "video" else "the configured limit"
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max for {kind}: {max_mb} MB.",
        )
    # LinkedIn rule: can't mix images + videos in one post — enforce here
    other_kinds = (
        db.query(Attachment.file_type)
        .filter(Attachment.post_id == post_id, Attachment.is_media == True)
        .distinct()
        .all()
    )
    other_kinds = {row[0].value for row in other_kinds}
    target_type = AttachmentType.IMAGE if kind == "image" else AttachmentType.VIDEO
    if other_kinds and target_type.value not in other_kinds:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot mix images and videos in one post. Existing: {other_kinds}",
        )
    storage = StorageService()
    saved_path, size = storage.save_upload(BytesIO(contents), file.filename or "upload")
    attachment = Attachment(
        post_id=post_id,
        file_type=target_type,
        file_path=saved_path,
        file_size=size,
        original_filename=file.filename,
        mime_type=file.content_type,
        extracted_text=None,  # No text extraction for media
        is_media=True,        # The key flag!
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    logger.info(f"Media attachment {attachment.id} added to post {post_id}")
    return _build_response(attachment)
# ============== LINK INGESTION (unchanged) ==============
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
        is_media=False,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return _build_response(attachment)
# ============== NEW PHASE 9.5: DOWNLOAD (for manual mode) ==============
@router.get(
    "/{attachment_id}/download",
    summary="Download raw attachment file (for manual posting)",
)
def download_attachment(
    attachment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the raw file. Useful in Manual Mode when user needs to upload to LinkedIn themselves."""
    att = (
        db.query(Attachment)
        .join(Post, Attachment.post_id == Post.id)
        .filter(Attachment.id == attachment_id, Post.user_id == user.id)
        .first()
    )
    if not att or not att.file_path:
        raise HTTPException(status_code=404, detail="File not found")
    if not os.path.exists(att.file_path):
        raise HTTPException(status_code=404, detail="File missing on disk")
    return FileResponse(
        path=att.file_path,
        filename=att.original_filename or os.path.basename(att.file_path),
        media_type=att.mime_type or "application/octet-stream",
    )
# ============== DELETE (unchanged) ==============
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