from datetime import datetime, timezone
import re
import unicodedata
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import assert_owner_or_admin, get_current_user
from app.database.session import get_db
from app.models.analysis_job import AnalysisJob
from app.models.analysis_result import AnalysisResult
from app.models.candidate import Candidate
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.api.uploads import candidate_name_from_filename
from app.storage.factory import get_storage_service
from app.schemas.job import (
    AttachFileRequest,
    CandidateRankingItem,
    CandidateResponse,
    JobCreateRequest,
    JobCreateResponse,
    JobResponse,
    ResultResponse,
)
from app.services.job_event_service import create_job_event
from app.services.report_pdf import build_candidate_report_pdf
from app.services.sqs_service import sqs_service

router = APIRouter(prefix="/jobs", tags=["Jobs"])
storage_service = get_storage_service()


def _safe_download_filename(value: str | None, fallback: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    safe = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return safe or fallback


def _matches_fit(fit_key: str, score: float | None, status: str) -> bool:
    """Match a candidate against a fit bucket used by the UI filter.

    Buckets mirror the frontend thresholds: excellent >=85, strong 70-84,
    medium 55-69, weak <55, failed = analysis failed.
    """
    if fit_key == "failed":
        return status == "failed"
    if score is None:
        return False
    if fit_key == "excellent":
        return score >= 85
    if fit_key == "strong":
        return 70 <= score < 85
    if fit_key == "medium":
        return 55 <= score < 70
    if fit_key == "weak":
        return score < 55
    return True


def candidate_response(candidate: Candidate) -> CandidateResponse:
    return CandidateResponse(
        id=str(candidate.id),
        job_id=str(candidate.job_id),
        user_id=str(candidate.user_id),
        cv_file_id=str(candidate.cv_file_id) if candidate.cv_file_id else None,
        name=candidate.name,
        email=candidate.email,
        status=candidate.status,
        recommendation=candidate.recommendation,
        error_code=candidate.error_code,
        error_message=candidate.error_message,
        created_at=candidate.created_at,
        queued_at=candidate.queued_at,
        started_at=candidate.started_at,
        completed_at=candidate.completed_at,
        failed_at=candidate.failed_at,
    )


def get_result_for_candidate(db: Session, candidate_id: UUID) -> AnalysisResult | None:
    return db.query(AnalysisResult).filter(AnalysisResult.candidate_id == candidate_id).first()


def result_to_response(job: AnalysisJob, result: AnalysisResult) -> ResultResponse:
    raw = result.raw_matching_result or {}
    skill_score = float(result.skill_score) if result.skill_score is not None else 0.0
    experience_score = float(result.experience_score) if result.experience_score is not None else 50.0
    education_score = float(result.education_score) if result.education_score is not None else 50.0
    keyword_score = raw.get("keyword_score", skill_score)
    cv_quality_score = raw.get("cv_quality_score", 70.0)

    compatibility = raw.get("compatibility", {})
    if not compatibility:
        from app.matching.engine import get_compatibility_level
        compatibility = get_compatibility_level(float(result.matching_score))

    score_breakdown = raw.get("score_breakdown", {
        "skill_match": {"score": skill_score, "weight": 35, "description": "Mức độ khớp kỹ năng"},
        "role_match": {"score": raw.get("role_compatibility", 60.0), "weight": 20, "description": "Mức độ phù hợp cấp bậc"},
        "domain_match": {"score": raw.get("domain_compatibility", 50.0), "weight": 15, "description": "Mức độ phù hợp lĩnh vực"},
        "experience_match": {"score": experience_score, "weight": 15, "description": "Mức độ phù hợp kinh nghiệm"},
        "education_match": {"score": education_score, "weight": 5, "description": "Mức độ phù hợp học vấn"},
        "keyword_match": {"score": keyword_score, "weight": 5, "description": "Mức độ khớp từ khóa"},
        "cv_quality": {"score": cv_quality_score, "weight": 5, "description": "Chất lượng CV"},
    })

    confidence = raw.get("confidence", {})
    confidence_score = float(confidence.get("score", 0.82)) if isinstance(confidence, dict) else 0.82

    return ResultResponse(
        job_id=str(job.id),
        candidate_id=str(result.candidate_id) if result.candidate_id else None,
        compatibility={
            "overall_score": float(result.matching_score),
            "level": compatibility.get("level", "N/A"),
            "recommendation": compatibility.get("recommendation", "N/A"),
            "message": compatibility.get("message", ""),
            "confidence": confidence_score,
        },
        score_breakdown=score_breakdown,
        skills_analysis={
            "matched_skills": result.matched_skills or [],
            "missing_skills": result.missing_skills or [],
            "extra_skills": result.extra_skills or [],
            "skill_match_ratio": skill_score,
            "matched_must_have": raw.get("matched_must_have", []),
            "missing_must_have": raw.get("missing_must_have", []),
            "matched_nice_to_have": raw.get("matched_nice_to_have", []),
            "missing_nice_to_have": raw.get("missing_nice_to_have", []),
        },
        candidate_summary={
            "summary": result.summary,
            "strengths": result.strengths or [],
            "weaknesses": result.weaknesses or [],
            "risk_flags": raw.get("risk_flags", []),
        },
        recommendations={
            "for_recruiter": raw.get("recommendations", {}).get("for_recruiter", []) if raw else [],
            "for_candidate": result.improvement_suggestions or [],
        },
        interview_questions=result.interview_questions or [],
        alternative_roles=raw.get("alternative_roles", []) if raw else [],
        warnings=raw.get("warnings", []) if raw else [],
        extracted_text=raw.get("extracted_text"),
        metadata={
            "ai_provider": result.ai_provider,
            "ai_model": result.ai_model,
            "processing_time_seconds": float(result.processing_time_seconds) if result.processing_time_seconds is not None else None,
            "confidence_level": confidence.get("level") if isinstance(confidence, dict) else None,
            "role_match": raw.get("role_compatibility"),
            "domain_match": raw.get("domain_compatibility"),
            "candidate_years": raw.get("candidate_years"),
            "required_years": raw.get("required_years"),
            "cv_role_level": raw.get("cv_role_level"),
            "jd_role_level": raw.get("jd_role_level"),
            "cv_domains": raw.get("cv_domains", []),
            "jd_domains": raw.get("jd_domains", []),
        },
    )


def to_job_response(db: Session, job: AnalysisJob) -> JobResponse:
    candidate_count = db.query(Candidate).filter(Candidate.job_id == job.id).count()
    analyzed_count = db.query(Candidate).filter(Candidate.job_id == job.id, Candidate.status == "completed").count()
    average_score = db.query(func.avg(AnalysisResult.matching_score)).filter(AnalysisResult.job_id == job.id).scalar()
    best_result = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.job_id == job.id)
        .order_by(AnalysisResult.matching_score.desc())
        .first()
    )
    best_candidate_name = None
    if best_result and best_result.candidate_id:
        best_candidate = db.query(Candidate).filter(Candidate.id == best_result.candidate_id).first()
        best_candidate_name = best_candidate.name if best_candidate else None

    return JobResponse(
        id=str(job.id),
        user_id=str(job.user_id),
        title=job.title,
        description=job.description,
        status=job.status,
        cv_file_id=str(job.cv_file_id) if job.cv_file_id else None,
        jd_file_id=str(job.jd_file_id) if job.jd_file_id else None,
        candidate_count=candidate_count,
        analyzed_count=analyzed_count,
        average_score=float(average_score) if average_score is not None else None,
        best_candidate_name=best_candidate_name,
        best_score=float(best_result.matching_score) if best_result else None,
        error_code=job.error_code,
        error_message=job.error_message,
        retry_count=job.retry_count or 0,
        created_at=job.created_at,
        queued_at=job.queued_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        failed_at=job.failed_at,
    )


def ensure_legacy_candidate(db: Session, job: AnalysisJob, current_user: User) -> Candidate | None:
    existing = db.query(Candidate).filter(Candidate.job_id == job.id).first()
    if existing or not job.cv_file_id:
        return existing

    cv_file = db.query(UploadedFile).filter(UploadedFile.id == job.cv_file_id).first()
    candidate = Candidate(
        user_id=current_user.id,
        job_id=job.id,
        cv_file_id=job.cv_file_id,
        name=cv_file.original_filename if cv_file else "Candidate",
        status="uploaded",
    )
    db.add(candidate)
    db.flush()
    return candidate


@router.post("", response_model=JobCreateResponse, status_code=201)
def create_job(
    payload: JobCreateRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = AnalysisJob(
        user_id=current_user.id,
        title=payload.title if payload else None,
        description=payload.description if payload else None,
        status="uploaded",
    )
    db.add(job)
    db.flush()
    create_job_event(db, job.id, "job_created", None, "uploaded", "Đã tạo công việc")
    db.commit()
    db.refresh(job)
    return JobCreateResponse(job_id=str(job.id), status=job.status)


@router.post("/{job_id}/attach-file")
def attach_file(
    job_id: UUID,
    payload: AttachFileRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gắn một tệp đã tải lên trước đó vào công việc hiện tại (tái sử dụng).

    Không sao chép tệp — chỉ trỏ candidate (CV) hoặc job.jd_file_id (JD) tới
    hàng uploaded_files đã tồn tại.
    """
    if payload.file_type not in ("cv", "jd"):
        raise HTTPException(status_code=400, detail="file_type phải là cv hoặc jd")

    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc")
    assert_owner_or_admin(job.user_id, current_user)
    if job.status not in ("uploaded", "failed", "cancelled"):
        raise HTTPException(status_code=409, detail="Không thể đính kèm tệp với trạng thái công việc hiện tại")

    src = db.query(UploadedFile).filter(UploadedFile.id == UUID(payload.file_id)).first()
    if not src:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp")
    assert_owner_or_admin(src.user_id, current_user)
    if src.upload_status != "uploaded":
        raise HTTPException(status_code=400, detail="Tệp không khả dụng")
    if src.file_type != payload.file_type:
        raise HTTPException(status_code=400, detail="Loại tệp không khớp")

    now = datetime.now(timezone.utc)
    candidate_id = None
    if payload.file_type == "cv":
        existing = (
            db.query(Candidate)
            .filter(Candidate.job_id == job.id, Candidate.cv_file_id == src.id)
            .first()
        )
        if existing:
            candidate = existing
        else:
            candidate = Candidate(
                user_id=current_user.id,
                job_id=job.id,
                cv_file_id=src.id,
                name=candidate_name_from_filename(src.original_filename),
                status="uploaded",
            )
            db.add(candidate)
            db.flush()
            if not job.cv_file_id:
                job.cv_file_id = src.id
        candidate_id = str(candidate.id)
    else:
        job.jd_file_id = src.id

    job.updated_at = now
    db.commit()
    return {
        "job_id": str(job.id),
        "file_id": str(src.id),
        "file_type": payload.file_type,
        "candidate_id": candidate_id,
    }


@router.get("")
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    query = db.query(AnalysisJob).filter(AnalysisJob.user_id == current_user.id)
    total = query.count()
    jobs = query.order_by(AnalysisJob.created_at.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": [to_job_response(db, job).model_dump() for job in jobs]}


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc")
    assert_owner_or_admin(job.user_id, current_user)
    return to_job_response(db, job)


@router.post("/{job_id}/enqueue")
async def enqueue_job(job_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc")
    assert_owner_or_admin(job.user_id, current_user)

    if not job.jd_file_id:
        raise HTTPException(status_code=400, detail="Cần tải lên JD trước khi phân tích")

    ensure_legacy_candidate(db, job, current_user)
    candidates = (
        db.query(Candidate)
        .filter(Candidate.job_id == job.id, Candidate.status.in_(["uploaded", "failed", "cancelled"]))
        .all()
    )
    if not candidates:
        raise HTTPException(status_code=400, detail="Cần ít nhất một CV ứng viên trước khi phân tích")

    jd_file = db.query(UploadedFile).filter(UploadedFile.id == job.jd_file_id).first()
    if not jd_file or jd_file.upload_status != "uploaded":
        raise HTTPException(status_code=400, detail="Tệp JD phải được tải lên")

    now = datetime.now(timezone.utc)
    old_status = job.status
    job.status = "queued"
    job.queued_at = now
    job.updated_at = now
    job.error_code = None
    job.error_message = None

    queue_messages = []
    for candidate in candidates:
        candidate.status = "queued"
        candidate.queued_at = now
        candidate.error_code = None
        candidate.error_message = None
        queue_messages.append(
            {
                "job_id": job.id,
                "candidate_id": candidate.id,
                "cv_file_id": candidate.cv_file_id,
                "jd_file_id": jd_file.id,
            }
        )

    create_job_event(db, job.id, "job_queued", old_status, "queued", f"Đã đưa {len(candidates)} ứng viên vào hàng đợi")
    db.commit()

    sent_candidate_ids = set()
    try:
        for message in queue_messages:
            await sqs_service.send_analysis_job(**message)
            sent_candidate_ids.add(message["candidate_id"])
    except Exception as exc:
        now = datetime.now(timezone.utc)
        unsent_candidate_ids = [
            message["candidate_id"]
            for message in queue_messages
            if message["candidate_id"] not in sent_candidate_ids
        ]
        if unsent_candidate_ids:
            db.query(Candidate).filter(Candidate.id.in_(unsent_candidate_ids)).update(
                {
                    Candidate.status: "uploaded",
                    Candidate.queued_at: None,
                    Candidate.error_code: "SQS_ENQUEUE_FAILED",
                    Candidate.error_message: str(exc)[:1000],
                    Candidate.updated_at: now,
                },
                synchronize_session=False,
            )
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if job:
            if not sent_candidate_ids:
                job.status = "uploaded"
                job.queued_at = None
            job.error_code = "SQS_ENQUEUE_FAILED"
            job.error_message = str(exc)[:1000]
            job.updated_at = now
            create_job_event(
                db,
                job.id,
                "job_enqueue_failed",
                "queued",
                job.status,
                "Không gửi được toàn bộ ứng viên vào hàng đợi SQS",
                {"sent": len(sent_candidate_ids), "unsent": len(unsent_candidate_ids)},
            )
        db.commit()
        raise HTTPException(status_code=503, detail="Không gửi được công việc vào hàng đợi. Vui lòng thử lại.") from exc

    return {"job_id": str(job.id), "status": job.status, "enqueued_candidates": len(candidates)}


@router.get("/{job_id}/candidates")
def list_candidates(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    fit: str | None = Query(default=None),
):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc")
    assert_owner_or_admin(job.user_id, current_user)

    candidates = db.query(Candidate).filter(Candidate.job_id == job.id).all()
    fit_key = fit.lower() if fit else None
    items = []
    for candidate in candidates:
        result = get_result_for_candidate(db, candidate.id)
        raw = result.raw_matching_result if result else {}
        compatibility = raw.get("compatibility", {}) if raw else {}
        confidence = raw.get("confidence", {}) if raw else {}
        recommendation = compatibility.get("recommendation") or candidate.recommendation
        score = float(result.matching_score) if result and result.matching_score is not None else None
        if fit_key and fit_key != "all" and not _matches_fit(fit_key, score, candidate.status):
            continue
        item_data = candidate_response(candidate).model_dump()
        item_data["recommendation"] = recommendation
        items.append(
            CandidateRankingItem(
                **item_data,
                rank=None,
                overall_score=float(result.matching_score) if result else None,
                skill_match=float(result.skill_score) if result and result.skill_score is not None else None,
                role_match=raw.get("role_compatibility") if raw else None,
                domain_match=raw.get("domain_compatibility") if raw else None,
                missing_skills=result.missing_skills if result else [],
                confidence=confidence.get("score") if isinstance(confidence, dict) else None,
                confidence_level=confidence.get("level") if isinstance(confidence, dict) else None,
                warnings=raw.get("warnings", []) if raw else [],
            )
        )

    items.sort(key=lambda item: item.overall_score if item.overall_score is not None else -1, reverse=True)
    for index, item in enumerate(items, start=1):
        item.rank = index if item.overall_score is not None else None
    return {"total": len(items), "items": [item.model_dump() for item in items]}


@router.get("/{job_id}/candidates/{candidate_id}", response_model=CandidateResponse)
def get_candidate(
    job_id: UUID,
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc")
    assert_owner_or_admin(job.user_id, current_user)

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id, Candidate.job_id == job.id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Không tìm thấy ứng viên")
    return candidate_response(candidate)


@router.get("/{job_id}/candidates/{candidate_id}/result", response_model=ResultResponse)
def get_candidate_result(
    job_id: UUID,
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc")
    assert_owner_or_admin(job.user_id, current_user)

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id, Candidate.job_id == job.id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Không tìm thấy ứng viên")

    result = get_result_for_candidate(db, candidate.id)
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy kết quả")
    return result_to_response(job, result)


@router.get("/{job_id}/candidates/{candidate_id}/report.pdf")
def download_candidate_report_pdf(
    job_id: UUID,
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc")
    assert_owner_or_admin(job.user_id, current_user)

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id, Candidate.job_id == job.id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Không tìm thấy ứng viên")

    result = get_result_for_candidate(db, candidate.id)
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy kết quả")

    response_data = result_to_response(job, result).model_dump()
    try:
        pdf_bytes = build_candidate_report_pdf(response_data, candidate.name)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    safe_name = _safe_download_filename(candidate.name, str(candidate.id)[:8])
    filename = f"candidate-report-{safe_name}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _delete_candidate_cv_file(db: Session, candidate: Candidate) -> None:
    """Xóa tệp CV gắn với ứng viên (soft-delete + tệp vật lý nếu không dùng chung).

    CV chứa thông tin cá nhân nên nên được gỡ khi xóa lần test. Chỉ xóa tệp
    vật lý khi không còn bản ghi nào khác trỏ tới cùng storage_path.
    """
    if not candidate.cv_file_id:
        return
    cv_file = db.query(UploadedFile).filter(UploadedFile.id == candidate.cv_file_id).first()
    if not cv_file or cv_file.upload_status == "deleted":
        return

    cv_file.upload_status = "deleted"
    cv_file.deleted_at = datetime.now(timezone.utc)

    others = (
        db.query(UploadedFile)
        .filter(
            UploadedFile.storage_path == cv_file.storage_path,
            UploadedFile.id != cv_file.id,
            UploadedFile.upload_status != "deleted",
        )
        .count()
    )
    if others == 0:
        try:
            storage_service.delete(cv_file.storage_path)
        except Exception:
            pass

    db.query(AnalysisJob).filter(AnalysisJob.cv_file_id == cv_file.id).update(
        {"cv_file_id": None, "updated_at": datetime.now(timezone.utc)},
        synchronize_session=False,
    )


@router.delete("/{job_id}/candidates/{candidate_id}")
def delete_candidate(
    job_id: UUID,
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Xóa một lần test (ứng viên) khỏi công việc.

    Xóa ứng viên sẽ cascade xóa kết quả phân tích; tệp CV kèm theo cũng được
    gỡ. Nếu công việc không còn ứng viên nào, cập nhật lại trạng thái công việc.
    """
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc")
    assert_owner_or_admin(job.user_id, current_user)

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id, Candidate.job_id == job.id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Không tìm thấy ứng viên")

    _delete_candidate_cv_file(db, candidate)
    db.delete(candidate)
    db.flush()

    # Nếu không còn ứng viên nào, đưa công việc về trạng thái an toàn.
    remaining = db.query(Candidate).filter(Candidate.job_id == job.id).count()
    if remaining == 0 and job.status not in ("uploaded", "queued", "processing"):
        job.status = "uploaded"
        job.updated_at = datetime.now(timezone.utc)

    db.commit()
    return {"message": "Đã xóa lần test", "remaining_candidates": remaining}


@router.get("/{job_id}/result", response_model=ResultResponse)
def get_job_result(job_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc")
    assert_owner_or_admin(job.user_id, current_user)

    result = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.job_id == job.id)
        .order_by(AnalysisResult.matching_score.desc())
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy kết quả")
    return result_to_response(job, result)


@router.delete("/{job_id}")
def cancel_job(job_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc")
    assert_owner_or_admin(job.user_id, current_user)
    if job.status in ["completed", "processing"]:
        raise HTTPException(status_code=409, detail="Không thể hủy công việc đã hoàn tất hoặc đang xử lý")
    old_status = job.status
    job.status = "cancelled"
    job.updated_at = datetime.now(timezone.utc)
    db.query(Candidate).filter(Candidate.job_id == job.id, Candidate.status.in_(["uploaded", "queued"])).update(
        {"status": "cancelled", "updated_at": datetime.now(timezone.utc)},
        synchronize_session=False,
    )
    create_job_event(db, job.id, "job_cancelled", old_status, "cancelled", "Đã hủy công việc")
    db.commit()
    return {"message": "Đã hủy công việc"}
