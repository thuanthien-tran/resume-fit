from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import Response
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.api.dependencies import assert_owner_or_admin, get_current_user
from app.core.config import settings
from app.database.session import get_db
from app.models.analysis_job import AnalysisJob
from app.models.candidate import Candidate
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.schemas.upload import (
    CompleteUploadRequest,
    PresignRequest,
    PresignResponse,
    SavedFileItem,
    UploadedFileResponse,
    UploadResponse,
)
from app.services.upload_service import (
    ALLOWED_EXTENSIONS,
    build_library_storage_path,
    build_storage_path,
    calculate_checksum,
    validate_file,
)
from app.services.document_classifier import validate_expected_type
from app.services.text_extractor import extract_text
from app.storage.factory import get_storage_service

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/uploads", tags=["Uploads"])
storage_service = get_storage_service()


def storage_bucket_name() -> str | None:
    return settings.s3_bucket if settings.storage_provider == "s3" else None


def storage_object_key(storage_path: str) -> str | None:
    return storage_path if settings.storage_provider == "s3" else None


def assert_document_type(content: bytes, filename: str, expected_type: str) -> None:
    """Xác minh nội dung tệp khớp loại kỳ vọng (cv/jd). Chặn nếu mismatch rõ.

    Best-effort: nếu không trích xuất được văn bản (ảnh scan, định dạng lạ) hoặc
    tín hiệu không rõ (unknown) thì cho qua — chỉ chặn khi phát hiện CHẮC CHẮN là
    loại ngược lại, tránh chặn oan các CV/JD trình bày bất thường.
    """
    try:
        text = extract_text(content, filename)
    except Exception:
        # Không đọc được văn bản ở bước upload -> không chặn; worker sẽ kiểm lại.
        return
    if not text or not text.strip():
        return

    result = validate_expected_type(text, expected_type)
    if result["validation_status"] != "mismatch":
        return

    expected_label = "CV" if expected_type == "cv" else "JD"
    detected_label = "CV" if result["detected_type"] == "cv" else "JD"
    raise HTTPException(
        status_code=422,
        detail={
            "code": "DOCUMENT_TYPE_MISMATCH",
            "message": f"Tệp \"{filename}\" có vẻ là {detected_label}, không phải {expected_label}.",
            "expected_type": expected_type,
            "detected_type": result["detected_type"],
            "confidence": result["confidence"],
            "reasons": result["reasons"],
        },
    )


def to_file_response(file: UploadedFile) -> UploadedFileResponse:
    return UploadedFileResponse(
        id=str(file.id),
        user_id=str(file.user_id),
        job_id=str(file.job_id) if file.job_id else None,
        file_type=file.file_type,
        original_filename=file.original_filename,
        display_name=file.display_name,
        storage_type=file.storage_type,
        storage_path=file.storage_path,
        mime_type=file.mime_type,
        file_size=file.file_size,
        checksum=file.checksum,
        upload_status=file.upload_status,
        created_at=file.created_at,
        uploaded_at=file.uploaded_at,
        deleted_at=file.deleted_at,
    )


def candidate_name_from_filename(filename: str) -> str:
    return Path(filename or "candidate").stem.replace("_", " ").strip() or "Candidate"


async def persist_upload(
    *,
    db: Session,
    current_user: User,
    job: AnalysisJob,
    file_type: str,
    file: UploadFile,
) -> tuple[UploadedFile, Candidate | None]:
    content = await validate_file(file)
    filename = file.filename or "uploaded_file"
    # Xác minh nội dung khớp loại ô (cv/jd) trước khi lưu.
    assert_document_type(content, filename, file_type)
    checksum = calculate_checksum(content)
    storage_path = build_storage_path(current_user.id, job.id, file_type, filename)
    saved_path = storage_service.save(storage_path, content)

    uploaded_file = UploadedFile(
        user_id=current_user.id,
        job_id=job.id,
        file_type=file_type,
        original_filename=filename,
        storage_type=settings.storage_provider,
        storage_path=saved_path,
        bucket_name=storage_bucket_name(),
        object_key=storage_object_key(saved_path),
        mime_type=file.content_type or "application/octet-stream",
        file_size=len(content),
        checksum=checksum,
        upload_status="uploaded",
    )
    db.add(uploaded_file)
    db.flush()

    candidate = None
    if file_type == "cv":
        candidate = Candidate(
            user_id=current_user.id,
            job_id=job.id,
            cv_file_id=uploaded_file.id,
            name=candidate_name_from_filename(filename),
            status="uploaded",
        )
        db.add(candidate)
        db.flush()
        if not job.cv_file_id:
            job.cv_file_id = uploaded_file.id
    else:
        job.jd_file_id = uploaded_file.id

    job.updated_at = datetime.now(timezone.utc)
    return uploaded_file, candidate


def upload_response(uploaded_file: UploadedFile, candidate: Candidate | None = None) -> UploadResponse:
    return UploadResponse(
        file_id=str(uploaded_file.id),
        job_id=str(uploaded_file.job_id),
        candidate_id=str(candidate.id) if candidate else None,
        file_type=uploaded_file.file_type,
        original_filename=uploaded_file.original_filename,
        display_name=uploaded_file.display_name,
        upload_status=uploaded_file.upload_status,
        file_size=uploaded_file.file_size,
        checksum=uploaded_file.checksum,
    )


@router.post("", response_model=UploadResponse, status_code=201)
async def upload_file(
    job_id: UUID = Form(...),
    file_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file_type not in ["cv", "jd"]:
        raise HTTPException(status_code=400, detail="file_type phải là cv hoặc jd")

    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc")
    assert_owner_or_admin(job.user_id, current_user)

    if job.status not in ["uploaded", "failed", "cancelled"]:
        raise HTTPException(status_code=409, detail="Không thể tải tệp lên với trạng thái công việc hiện tại")

    uploaded_file, candidate = await persist_upload(
        db=db,
        current_user=current_user,
        job=job,
        file_type=file_type,
        file=file,
    )
    db.commit()
    db.refresh(uploaded_file)
    if candidate:
        db.refresh(candidate)

    return upload_response(uploaded_file, candidate)


@router.post("/bulk-cv", status_code=201)
async def upload_multiple_cvs(
    job_id: UUID = Form(...),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc")
    assert_owner_or_admin(job.user_id, current_user)

    if job.status not in ["uploaded", "failed", "cancelled"]:
        raise HTTPException(status_code=409, detail="Không thể tải CV lên với trạng thái công việc hiện tại")
    if not files:
        raise HTTPException(status_code=400, detail="Cần ít nhất một tệp CV")

    # Xử lý từng tệp độc lập: một tệp lỗi không làm hỏng cả lô.
    # Mỗi tệp chạy trong một savepoint để lỗi DB không làm hỏng transaction chung.
    succeeded = []
    failed = []
    for file in files:
        filename = file.filename or "uploaded_file"
        try:
            with db.begin_nested():
                uploaded_file, candidate = await persist_upload(
                    db=db,
                    current_user=current_user,
                    job=job,
                    file_type="cv",
                    file=file,
                )
                succeeded.append(upload_response(uploaded_file, candidate).model_dump())
        except HTTPException as exc:
            failed.append({"original_filename": filename, "error": exc.detail})
        except Exception as exc:
            failed.append({"original_filename": filename, "error": str(exc)})

    db.commit()
    return {
        "total": len(files),
        "succeeded_count": len(succeeded),
        "failed_count": len(failed),
        "items": succeeded,
        "failed": failed,
    }


@router.post("/standalone", response_model=UploadResponse, status_code=201)
async def upload_standalone(
    file_type: str = Form(...),
    display_name: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tải lên một CV/JD vào thư viện mà không gắn với công việc nào.

    Dùng cho chức năng "Danh sách CV" / "Danh sách JD": người dùng tạo tài liệu
    độc lập, sau đó có thể tái sử dụng cho công việc bằng attach-file.
    """
    if file_type not in ("cv", "jd"):
        raise HTTPException(status_code=400, detail="file_type phải là cv hoặc jd")

    content = await validate_file(file)
    filename = file.filename or "uploaded_file"
    clean_display_name = (display_name or "").strip()[:255] or candidate_name_from_filename(filename)
    assert_document_type(content, filename, file_type)
    checksum = calculate_checksum(content)
    storage_path = build_library_storage_path(current_user.id, file_type, filename)
    saved_path = storage_service.save(storage_path, content)

    uploaded_file = UploadedFile(
        user_id=current_user.id,
        job_id=None,
        file_type=file_type,
        original_filename=filename,
        display_name=clean_display_name,
        storage_type=settings.storage_provider,
        storage_path=saved_path,
        bucket_name=storage_bucket_name(),
        object_key=storage_object_key(saved_path),
        mime_type=file.content_type or "application/octet-stream",
        file_size=len(content),
        checksum=checksum,
        upload_status="uploaded",
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)
    return UploadResponse(
        file_id=str(uploaded_file.id),
        job_id="",
        candidate_id=None,
        file_type=uploaded_file.file_type,
        original_filename=uploaded_file.original_filename,
        display_name=uploaded_file.display_name,
        upload_status=uploaded_file.upload_status,
        file_size=uploaded_file.file_size,
        checksum=uploaded_file.checksum,
    )


def _decode_presign_token(token: str, expected_action: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn")
    if payload.get("type") != "storage_presign" or payload.get("action") != expected_action:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")
    storage_path = payload.get("storage_path")
    if not storage_path:
        raise HTTPException(status_code=401, detail="Token thiếu storage_path")
    return storage_path


@router.post("/presign", response_model=PresignResponse)
def presign_upload(
    payload: PresignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cấp URL để client upload file trực tiếp lên storage (S3 thật / mô phỏng local)."""
    if payload.file_type not in ("cv", "jd"):
        raise HTTPException(status_code=400, detail="file_type phải là cv hoặc jd")

    ext = Path(payload.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Định dạng tệp không được hỗ trợ: {ext}")

    job = db.query(AnalysisJob).filter(AnalysisJob.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc")
    assert_owner_or_admin(job.user_id, current_user)
    if job.status not in ("uploaded", "failed", "cancelled"):
        raise HTTPException(status_code=409, detail="Không thể tải tệp lên với trạng thái công việc hiện tại")

    storage_path = build_storage_path(current_user.id, job.id, payload.file_type, payload.filename)
    upload_url = storage_service.generate_presigned_upload_url(
        storage_path, payload.content_type, settings.presign_expiry_seconds
    )
    return PresignResponse(
        storage_path=storage_path,
        upload_url=upload_url,
        file_type=payload.file_type,
        original_filename=payload.filename,
    )


@router.put("/local-put")
async def local_put(token: str, request: Request):
    """Endpoint mô phỏng S3 PUT ở môi trường local. Trên AWS, client PUT thẳng lên S3."""
    storage_path = _decode_presign_token(token, "put")
    content = await request.body()
    if not content:
        raise HTTPException(status_code=400, detail="Tệp rỗng")
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="Tệp quá lớn")
    storage_service.save(storage_path, content)
    return {"storage_path": storage_path, "file_size": len(content)}


@router.post("/complete", response_model=UploadResponse, status_code=201)
def complete_upload(
    payload: CompleteUploadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Xác nhận file đã upload xong: đọc lại từ storage, tạo bản ghi UploadedFile + Candidate."""
    if payload.file_type not in ("cv", "jd"):
        raise HTTPException(status_code=400, detail="file_type phải là cv hoặc jd")

    job = db.query(AnalysisJob).filter(AnalysisJob.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc")
    assert_owner_or_admin(job.user_id, current_user)
    if job.status not in ("uploaded", "failed", "cancelled"):
        raise HTTPException(status_code=409, detail="Không thể tải tệp lên với trạng thái công việc hiện tại")

    if not storage_service.exists(payload.storage_path):
        raise HTTPException(status_code=400, detail="Chưa tìm thấy tệp trên storage")
    content = storage_service.read(payload.storage_path)
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="Tệp quá lớn")
    assert_document_type(content, payload.original_filename, payload.file_type)

    uploaded_file = UploadedFile(
        user_id=current_user.id,
        job_id=job.id,
        file_type=payload.file_type,
        original_filename=payload.original_filename,
        storage_type=settings.storage_provider,
        storage_path=payload.storage_path,
        bucket_name=storage_bucket_name(),
        object_key=storage_object_key(payload.storage_path),
        mime_type=payload.mime_type,
        file_size=len(content),
        checksum=calculate_checksum(content),
        upload_status="uploaded",
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add(uploaded_file)
    db.flush()

    candidate = None
    if payload.file_type == "cv":
        candidate = Candidate(
            user_id=current_user.id,
            job_id=job.id,
            cv_file_id=uploaded_file.id,
            name=candidate_name_from_filename(payload.original_filename),
            status="uploaded",
        )
        db.add(candidate)
        db.flush()
        if not job.cv_file_id:
            job.cv_file_id = uploaded_file.id
    else:
        job.jd_file_id = uploaded_file.id

    job.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(uploaded_file)
    if candidate:
        db.refresh(candidate)
    return upload_response(uploaded_file, candidate)


@router.get("", response_model=list[SavedFileItem])
def list_uploads(
    file_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Liệt kê các tệp đã tải lên của người dùng để tái sử dụng.

    Loại bỏ tệp đã xóa/lỗi và khử trùng lặp theo checksum (giữ bản mới nhất),
    để cùng một CV/JD tải lên nhiều lần chỉ hiện một dòng.
    """
    query = db.query(UploadedFile).filter(
        UploadedFile.user_id == current_user.id,
        UploadedFile.upload_status == "uploaded",
        UploadedFile.job_id.is_(None),
    )
    if file_type in ("cv", "jd"):
        query = query.filter(UploadedFile.file_type == file_type)

    rows = (
        query.distinct(UploadedFile.checksum)
        .order_by(UploadedFile.checksum, UploadedFile.created_at.desc())
        .all()
    )
    rows.sort(key=lambda f: f.created_at, reverse=True)

    # Lấy tên công việc cho các tệp có job_id (batch để tránh N+1 query).
    job_ids = {f.job_id for f in rows if f.job_id}
    titles: dict = {}
    if job_ids:
        jobs = db.query(AnalysisJob).filter(AnalysisJob.id.in_(job_ids)).all()
        titles = {job.id: job.title for job in jobs}

    return [
        SavedFileItem(
            id=str(f.id),
            original_filename=f.original_filename,
            display_name=f.display_name or candidate_name_from_filename(f.original_filename),
            file_type=f.file_type,
            file_size=f.file_size,
            created_at=f.created_at,
            job_id=str(f.job_id) if f.job_id else None,
            job_title=titles.get(f.job_id),
        )
        for f in rows
    ]


@router.get("/{file_id}", response_model=UploadedFileResponse)
def get_upload(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp")
    assert_owner_or_admin(uploaded_file.user_id, current_user)
    return to_file_response(uploaded_file)


@router.get("/{file_id}/content")
def get_upload_content(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trả về nội dung tệp gốc (ảnh/PDF/…) để xem trước.

    Chỉ chủ sở hữu hoặc admin truy cập được. Frontend fetch kèm token rồi tạo
    blob URL để hiển thị trong modal xem trước.
    """
    uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp")
    assert_owner_or_admin(uploaded_file.user_id, current_user)
    if uploaded_file.upload_status == "deleted":
        raise HTTPException(status_code=410, detail="Tệp đã bị xóa")

    try:
        content = storage_service.read(uploaded_file.storage_path)
    except Exception:
        raise HTTPException(status_code=404, detail="Không đọc được nội dung tệp")

    return Response(
        content=content,
        media_type=uploaded_file.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{uploaded_file.original_filename}"'},
    )


@router.delete("/{file_id}")
def delete_upload(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp")
    assert_owner_or_admin(uploaded_file.user_id, current_user)

    uploaded_file.upload_status = "deleted"
    uploaded_file.deleted_at = datetime.now(timezone.utc)

    # Xoá tệp vật lý khỏi storage (dữ liệu CV/JD chứa thông tin cá nhân).
    # Chỉ xoá khi không còn bản ghi nào khác trỏ tới cùng storage_path
    # (cùng tên tệp tải lên lại sẽ ghi đè và dùng chung path).
    others_sharing_path = (
        db.query(UploadedFile)
        .filter(
            UploadedFile.storage_path == uploaded_file.storage_path,
            UploadedFile.id != uploaded_file.id,
            UploadedFile.upload_status != "deleted",
        )
        .count()
    )
    if others_sharing_path == 0:
        try:
            storage_service.delete(uploaded_file.storage_path)
        except Exception:
            # Không chặn thao tác xoá logic nếu xoá tệp vật lý thất bại;
            # bản ghi vẫn được đánh dấu deleted để không còn dùng nữa.
            pass

    # Gỡ mọi tham chiếu tới file này để job không còn trỏ vào tệp đã xoá.
    if uploaded_file.file_type == "jd":
        db.query(AnalysisJob).filter(AnalysisJob.jd_file_id == uploaded_file.id).update(
            {"jd_file_id": None, "updated_at": datetime.now(timezone.utc)},
            synchronize_session=False,
        )
    else:  # cv
        db.query(AnalysisJob).filter(AnalysisJob.cv_file_id == uploaded_file.id).update(
            {"cv_file_id": None, "updated_at": datetime.now(timezone.utc)},
            synchronize_session=False,
        )
        # Xoá ứng viên chưa phân tích gắn với CV này (giữ lại ứng viên đã có kết quả).
        db.query(Candidate).filter(
            Candidate.cv_file_id == uploaded_file.id,
            Candidate.status.in_(["uploaded", "queued", "cancelled", "failed"]),
        ).delete(synchronize_session=False)

    db.commit()
    return {"message": "Đã xóa tệp"}
