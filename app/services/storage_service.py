"""Storage service — abstracts file storage. Local now, S3 later."""
import os
import shutil
from typing import BinaryIO, Tuple
from app.utils.file_utils import safe_filename, ensure_upload_dir
from app.utils.logger import logger
class StorageService:
    def __init__(self):
        self.upload_dir = ensure_upload_dir()
    def save_upload(self, file_obj: BinaryIO, original_filename: str) -> Tuple[str, int]:
        filename = safe_filename(original_filename)
        full_path = os.path.join(self.upload_dir, filename)
        file_obj.seek(0)
        with open(full_path, "wb") as out:
            shutil.copyfileobj(file_obj, out)
        size = os.path.getsize(full_path)
        logger.info(f"Saved upload: {full_path} ({size} bytes)")
        return full_path, size
    def delete_file(self, path: str) -> bool:
        try:
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"Deleted file: {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete {path}: {e}")
            return False
    def read_file(self, path: str) -> bytes:
        with open(path, "rb") as f:
            return f.read()