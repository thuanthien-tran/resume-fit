import hashlib
import re
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile

from app.core.config import settings

# Chỉ nhận tệp văn bản. Ảnh (PNG/JPG/...) bị loại vì OCR không đọc được chữ
# trong ảnh CV/JD một cách đáng tin cậy.
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".rtf"}

# Chữ ký nội dung (magic bytes) theo từng đuôi tệp. Kiểm tra nội dung thật
# thay vì tin vào đuôi tệp hay Content-Type do client gửi lên.
# .docx/.pptx là container ZIP (OOXML) nên chung chữ ký PK\x03\x04.
FILE_SIGNATURES: dict[str, tuple[bytes, ...]] = {
    ".pdf": (b"%PDF",),
    ".docx": (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"),
    ".pptx": (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"),
    ".rtf": (b"{\\rtf",),
    # .txt không có magic bytes cố định -> không kiểm tra chữ ký.
}


def _matches_signature(ext: str, content: bytes) -> bool:
    """Kiểm tra nội dung có khớp chữ ký magic bytes của đuôi tệp không."""
    signatures = FILE_SIGNATURES.get(ext)
    if signatures is None:  # ví dụ .txt -> bỏ qua kiểm tra chữ ký
        return True
    return any(content.startswith(sig) for sig in signatures)


def safe_filename(filename: str) -> str:
    filename = filename.strip().replace(" ", "_")
    filename = re.sub(r"[^a-zA-Z0-9._-]", "", filename)
    return filename or "uploaded_file"


def build_storage_path(user_id: UUID, job_id: UUID, file_type: str, filename: str) -> str:
    clean_name = safe_filename(filename)
    return f"users/{user_id}/jobs/{job_id}/{file_type}/{clean_name}"


def build_library_storage_path(user_id: UUID, file_type: str, filename: str) -> str:
    """Đường dẫn cho tệp trong thư viện CV/JD (không gắn với công việc nào)."""
    clean_name = safe_filename(filename)
    return f"users/{user_id}/library/{file_type}/{clean_name}"


async def validate_file(file: UploadFile) -> bytes:
    original_filename = file.filename or ""
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Định dạng tệp không được hỗ trợ: {ext}. "
                   "Chỉ nhận tệp văn bản: PDF, DOCX, PPTX, TXT, RTF. "
                   "Tệp ảnh không được hỗ trợ vì không đọc được chữ trong ảnh.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Tệp rỗng")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="Tệp quá lớn")

    # Kiểm tra nội dung thật (magic bytes) khớp với đuôi tệp, chống việc đổi
    # đuôi tệp để vượt qua kiểm tra (ví dụ .exe đổi tên thành .pdf).
    if not _matches_signature(ext, content):
        raise HTTPException(
            status_code=400,
            detail=f"Nội dung tệp không khớp với định dạng {ext}. "
                   "Tệp có thể bị hỏng hoặc đã bị đổi đuôi.",
        )

    return content


def calculate_checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
