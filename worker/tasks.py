import logging
import time
from datetime import datetime, timezone
from uuid import UUID

from botocore.exceptions import ConnectionClosedError, ConnectTimeoutError, EndpointConnectionError, ReadTimeoutError
from sqlalchemy.exc import IntegrityError, InterfaceError, OperationalError

from app.ai.factory import get_ai_service
from app.core.config import settings
from app.database.session import SessionLocal
from app.matching.engine import calculate_matching
from app.services.document_classifier import validate_expected_type
from app.models.analysis_job import AnalysisJob
from app.models.analysis_result import AnalysisResult
from app.models.candidate import Candidate
from app.models.uploaded_file import UploadedFile
from app.services.job_event_service import create_job_event
from app.services.text_extractor import extract_text
from app.storage.factory import get_storage_service

logger = logging.getLogger(__name__)


# Lỗi tạm thời -> nên retry. Lỗi dữ liệu (ValueError: parse/empty/unsupported)
# -> fail luôn vì retry cũng không đổi kết quả.
TRANSIENT_ERRORS = (
    OperationalError,
    InterfaceError,
    ConnectionError,
    TimeoutError,
    EndpointConnectionError,
    ConnectTimeoutError,
    ReadTimeoutError,
    ConnectionClosedError,
)
MAX_INTERNAL_RETRIES = 3
DEFAULT_RETRY_DELAY_SECONDS = 30


class RetryableAnalysisError(Exception):
    """Signal the SQS worker to leave the message in the queue for redelivery."""


def is_transient_error(exc: Exception) -> bool:
    """Phân biệt lỗi tạm thời (retry được) với lỗi dữ liệu (fail luôn)."""
    return isinstance(exc, TRANSIENT_ERRORS)


def _reset_for_retry(db, job_id: UUID, candidate_id: UUID | None, exc: Exception) -> None:
    """Đưa candidate/job về trạng thái chờ trước khi retry.

    Đầu task chỉ xử lý candidate ở trạng thái 'queued', nên phải reset khỏi
    'processing' để lần retry sau không bị bỏ qua. Ghi lại lỗi tạm thời nhưng
    KHÔNG đánh dấu thất bại.
    """
    now = datetime.now(timezone.utc)
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first() if candidate_id else None
    if candidate:
        candidate.status = "queued"
        candidate.error_code = exc.__class__.__name__
        candidate.error_message = str(exc)[:1000]
        candidate.started_at = None
        candidate.updated_at = now
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if job:
        # Giữ job ở 'processing'; chỉ ghi nhận lỗi tạm thời để theo dõi.
        job.error_code = exc.__class__.__name__
        job.error_message = str(exc)[:1000]
        job.updated_at = now
    db.commit()


def build_parse_quality(cv_text: str, jd_text: str, matching_result: dict) -> tuple[dict, list[str]]:
    warnings: list[str] = []
    score = 100

    if len(cv_text.strip()) < 300:
        score -= 25
        warnings.append("Nội dung CV quá ngắn. Độ tin cậy của kết quả có thể thấp.")
    if len(jd_text.strip()) < 300:
        score -= 15
        warnings.append("Nội dung JD quá ngắn. Việc trích xuất yêu cầu có thể chưa đầy đủ.")
    if not matching_result.get("matched_skills") and not matching_result.get("missing_skills"):
        score -= 25
        warnings.append("Không phát hiện được kỹ năng nào từ CV/JD.")
    if matching_result.get("candidate_years") is None:
        score -= 10
        warnings.append("Không phát hiện rõ số năm kinh nghiệm của ứng viên.")
    if matching_result.get("cv_role_level") in [None, "unknown"]:
        score -= 10
        warnings.append("Không phát hiện rõ cấp bậc của ứng viên.")
    if not matching_result.get("cv_domains"):
        score -= 10
        warnings.append("Không phát hiện rõ lĩnh vực chuyên môn của ứng viên.")

    score = max(score, 0)
    if score >= 75:
        level = "Cao"
    elif score >= 50:
        level = "Trung bình"
    else:
        level = "Thấp"
        warnings.append("Kết quả có độ tin cậy thấp. Vui lòng xem lại văn bản trích xuất trước khi ra quyết định.")

    return {"score": round(score / 100, 2), "level": level}, warnings


def current_ai_model() -> str:
    if settings.ai_provider == "ollama":
        return settings.ollama_model
    if settings.ai_provider == "xai":
        return settings.xai_model
    return settings.ai_model


def upsert_result(db, *, job, candidate, matching_result, ai_result, ai_provider, ai_model, processing_time):
    result = None
    if candidate:
        result = db.query(AnalysisResult).filter(AnalysisResult.candidate_id == candidate.id).first()
    if not result:
        result = db.query(AnalysisResult).filter(
            AnalysisResult.job_id == job.id,
            AnalysisResult.candidate_id.is_(None),
        ).first() if not candidate else None
    if not result:
        result = AnalysisResult(job_id=job.id, candidate_id=candidate.id if candidate else None)
        db.add(result)

    result.job_id = job.id
    result.candidate_id = candidate.id if candidate else None
    result.matching_score = matching_result["matching_score"]
    result.skill_score = matching_result["skill_score"]
    result.experience_score = matching_result["experience_score"]
    result.education_score = matching_result["education_score"]
    result.matched_skills = matching_result["matched_skills"]
    result.missing_skills = matching_result["missing_skills"]
    result.extra_skills = matching_result["extra_skills"]
    result.summary = ai_result.get("summary")
    result.strengths = ai_result.get("strengths", [])
    result.weaknesses = ai_result.get("weaknesses", [])
    result.improvement_suggestions = ai_result.get("improvement_suggestions", [])
    result.interview_questions = ai_result.get("interview_questions", [])
    result.raw_matching_result = matching_result
    result.ai_provider = ai_provider
    result.ai_model = ai_model
    result.processing_time_seconds = processing_time
    return result


def update_job_terminal_status(db, job: AnalysisJob) -> None:
    candidates = db.query(Candidate).filter(Candidate.job_id == job.id).all()
    if not candidates:
        return

    active_statuses = {"uploaded", "queued", "processing"}
    if any(candidate.status in active_statuses for candidate in candidates):
        return

    # Tất cả ứng viên đã ở trạng thái cuối (completed/failed/cancelled).
    # Cancelled được xem là trung tính, không tính là thất bại.
    completed = sum(1 for c in candidates if c.status == "completed")
    failed = sum(1 for c in candidates if c.status == "failed")

    old_status = job.status
    now = datetime.now(timezone.utc)
    if completed and failed:
        job.status = "partial_completed"
        job.completed_at = now
        create_job_event(
            db, job.id, "job_partial_completed", old_status, "partial_completed",
            f"Hoàn tất {completed} ứng viên, {failed} ứng viên thất bại",
        )
    elif completed:
        job.status = "completed"
        job.completed_at = now
        create_job_event(db, job.id, "job_completed", old_status, "completed", "Đã hoàn tất phân tích ứng viên")
    elif failed:
        job.status = "failed"
        job.failed_at = now
        create_job_event(db, job.id, "job_failed", old_status, "failed", "Tất cả phân tích ứng viên đều thất bại")
    else:
        # Không có completed lẫn failed -> tất cả bị hủy.
        job.status = "cancelled"
        create_job_event(db, job.id, "job_cancelled", old_status, "cancelled", "Tất cả ứng viên đã bị hủy")
    job.updated_at = now


def process_analysis_job(message: dict):
    db = SessionLocal()
    start_time = time.time()
    job_id = UUID(message["job_id"])
    candidate_id = UUID(message["candidate_id"]) if message.get("candidate_id") else None

    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            logger.warning("Job not found: %s", job_id)
            return

        candidate = None
        if candidate_id:
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id, Candidate.job_id == job.id).first()
            if not candidate:
                logger.warning("Candidate not found: %s", candidate_id)
                return
            if candidate.status == "completed":
                logger.info("Candidate already completed, skip: %s", candidate_id)
                return
            if candidate.status != "queued":
                logger.info("Candidate is not queued, skip: %s status=%s", candidate_id, candidate.status)
                return
        elif job.status == "completed":
            logger.info("Job already completed, skip: %s", job_id)
            return

        old_status = job.status
        job.status = "processing"
        job.started_at = job.started_at or datetime.now(timezone.utc)
        job.updated_at = datetime.now(timezone.utc)
        if candidate:
            candidate.status = "processing"
            candidate.started_at = datetime.now(timezone.utc)
            candidate.updated_at = datetime.now(timezone.utc)
        create_job_event(db, job.id, "job_processing", old_status, "processing", "Worker bắt đầu xử lý")
        db.commit()

        logger.info("worker_download_cv_started", extra={"job_id": str(job_id), "candidate_id": str(candidate_id)})
        storage_service = get_storage_service()
        cv_file_id = candidate.cv_file_id if candidate else UUID(message["cv_file_id"])
        jd_file_id = UUID(message["jd_file_id"])
        cv_file = db.query(UploadedFile).filter(UploadedFile.id == cv_file_id).first()
        jd_file = db.query(UploadedFile).filter(UploadedFile.id == jd_file_id).first()
        if not cv_file or not jd_file:
            raise ValueError("CV or JD file metadata not found")

        cv_content = storage_service.read(cv_file.storage_path)
        logger.info("worker_download_jd_started", extra={"job_id": str(job_id), "candidate_id": str(candidate_id)})
        jd_content = storage_service.read(jd_file.storage_path)

        logger.info("worker_extract_text_started", extra={"job_id": str(job_id), "candidate_id": str(candidate_id)})
        cv_text = extract_text(cv_content, cv_file.storage_path)
        jd_text = extract_text(jd_content, jd_file.storage_path)
        if not cv_text.strip() or not jd_text.strip():
            raise ValueError("Could not extract text from CV or JD")

        # Lớp phòng thủ cuối: xác minh CV thật là CV và JD thật là JD trước khi
        # chấm điểm. Bắt cả tệp cũ, tệp gọi API trực tiếp, và tệp scan chỉ đọc
        # được văn bản ở bước này. Chỉ chặn khi phát hiện CHẮC CHẮN loại ngược lại.
        cv_check = validate_expected_type(cv_text, "cv")
        jd_check = validate_expected_type(jd_text, "jd")
        if cv_check["validation_status"] == "mismatch" or jd_check["validation_status"] == "mismatch":
            problems = []
            if cv_check["validation_status"] == "mismatch":
                problems.append("tệp CV có vẻ là JD")
            if jd_check["validation_status"] == "mismatch":
                problems.append("tệp JD có vẻ là CV")
            raise ValueError(
                "Không thể phân tích vì loại tài liệu không đúng: "
                + "; ".join(problems)
                + ". Vui lòng kiểm tra lại CV và JD đã tải đúng ô chưa."
            )

        logger.info("worker_matching_started", extra={"job_id": str(job_id), "candidate_id": str(candidate_id)})
        matching_result = calculate_matching(cv_text, jd_text)
        confidence, warnings = build_parse_quality(cv_text, jd_text, matching_result)
        matching_result["confidence"] = confidence
        matching_result["warnings"] = warnings
        matching_result["extracted_text"] = {
            "cv": cv_text[:12000],
            "jd": jd_text[:12000],
            "cv_truncated": len(cv_text) > 12000,
            "jd_truncated": len(jd_text) > 12000,
        }

        logger.info("worker_openai_started", extra={"job_id": str(job_id), "candidate_id": str(candidate_id)})
        ai_service = get_ai_service()
        try:
            ai_result = ai_service.generate_feedback(matching_result)
            ai_provider = settings.ai_provider
            ai_model = current_ai_model()
        except Exception as ai_exc:
            logger.exception("AI service failed, fallback to mock: %s", ai_exc)
            from app.ai.mock_ai import MockAIService

            ai_result = MockAIService().generate_feedback(matching_result)
            ai_provider = "mock_fallback"
            ai_model = "mock-v1"

        processing_time = round(time.time() - start_time, 3)

        matching_result["risk_flags"] = ai_result.get("risk_flags", [])
        matching_result["recommendations"] = ai_result.get("recommendations", {})
        matching_result["alternative_roles"] = ai_result.get("alternative_roles", [])

        logger.info("worker_save_database_started", extra={"job_id": str(job_id), "candidate_id": str(candidate_id)})
        result = upsert_result(
            db,
            job=job,
            candidate=candidate,
            matching_result=matching_result,
            ai_result=ai_result,
            ai_provider=ai_provider,
            ai_model=ai_model,
            processing_time=processing_time,
        )
        db.flush()

        if candidate:
            candidate.status = "completed"
            candidate.completed_at = datetime.now(timezone.utc)
            candidate.updated_at = datetime.now(timezone.utc)
            candidate.recommendation = matching_result.get("compatibility", {}).get("recommendation")

        update_job_terminal_status(db, job)
        db.commit()
        logger.info("Analysis completed: job=%s candidate=%s result=%s", job_id, candidate_id, result.id)

    except Exception as exc:
        db.rollback()

        # IntegrityError và các lỗi tạm thời (DB/kết nối/timeout) nên được retry;
        # lỗi dữ liệu (parse, file rỗng, định dạng không hỗ trợ) thì fail luôn.
        retry_count = int(message.get("_internal_retry_count", 0))
        retryable = isinstance(exc, IntegrityError) or is_transient_error(exc)
        retries_left = retry_count < MAX_INTERNAL_RETRIES

        if retryable and retries_left:
            _reset_for_retry(db, job_id, candidate_id, exc)
            logger.warning(
                "Transient error, retrying job=%s candidate=%s attempt=%s: %s",
                job_id, candidate_id, retry_count + 1, exc,
            )
            time.sleep(DEFAULT_RETRY_DELAY_SECONDS)
            retry_message = dict(message)
            retry_message["_internal_retry_count"] = retry_count + 1
            process_analysis_job(retry_message)
            return

        if retryable:
            _reset_for_retry(db, job_id, candidate_id, exc)
            logger.exception(
                "Transient analysis error exhausted internal retries: job=%s candidate=%s",
                job_id,
                candidate_id,
            )
            raise RetryableAnalysisError(
                f"Transient analysis error after {MAX_INTERNAL_RETRIES} internal retries"
            ) from exc

        # Lỗi dữ liệu không thể tự hết bằng retry -> đánh dấu thất bại và cho phép xóa SQS message.
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first() if candidate_id else None
        if candidate:
            candidate.status = "failed"
            candidate.error_code = exc.__class__.__name__
            candidate.error_message = str(exc)[:1000]
            candidate.failed_at = datetime.now(timezone.utc)
            candidate.updated_at = datetime.now(timezone.utc)
        if job:
            job.error_code = exc.__class__.__name__
            job.error_message = str(exc)[:1000]
            job.retry_count = (job.retry_count or 0) + 1
            update_job_terminal_status(db, job)
            create_job_event(
                db,
                job.id,
                "candidate_failed" if candidate else "job_failed",
                "processing",
                "failed",
                "Worker xử lý phân tích thất bại",
                {"candidate_id": str(candidate.id) if candidate else None, "error_code": job.error_code},
            )
            db.commit()
        logger.exception("Analysis failed: job=%s candidate=%s", job_id, candidate_id)

    finally:
        db.close()
