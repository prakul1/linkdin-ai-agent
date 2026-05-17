"""File handling utilities."""
import os
import uuid
from typing import Optional
from pathlib import Path
from app.config import settings
ALLOWED_PDF_TYPES = {"application/pdf"}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime"}  # NEW
ALLOWED_PDF_EXTENSIONS = {".pdf"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov"}  # NEW
# Size limits (MB)
MAX_VIDEO_SIZE_MB = 30  # LinkedIn limit consideration
def detect_file_kind(filename, content_type=None):
    """Returns 'pdf', 'image', 'video', or None."""
    ext = Path(filename).suffix.lower()
    if ext in ALLOWED_PDF_EXTENSIONS or content_type in ALLOWED_PDF_TYPES:
        return "pdf"
    if ext in ALLOWED_IMAGE_EXTENSIONS or content_type in ALLOWED_IMAGE_TYPES:
        return "image"
    if ext in ALLOWED_VIDEO_EXTENSIONS or content_type in ALLOWED_VIDEO_TYPES:
        return "video"
    return None
def validate_file_size(size_bytes, kind="default"):
    """Different size limits per kind."""
    if kind == "video":
        max_bytes = MAX_VIDEO_SIZE_MB * 1024 * 1024
    else:
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
    return size_bytes <= max_bytes
def safe_filename(original):
    base = os.path.basename(original)
    name, ext = os.path.splitext(base)
    safe_name = "".join(c for c in name if c.isalnum() or c in "._-")[:50]
    unique = uuid.uuid4().hex[:8]
    return f"{unique}-{safe_name}{ext.lower()}"
def ensure_upload_dir():
    path = os.path.abspath(settings.upload_dir)
    os.makedirs(path, exist_ok=True)
    return path