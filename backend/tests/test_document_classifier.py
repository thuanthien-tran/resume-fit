from app.services.document_classifier import detect_document_type, validate_expected_type


CV_SAMPLE = """
Nguyen Van A
email: vana@example.com | phone: +84 912 345 678 | github.com/vana
Career Objective: Backend engineer seeking a challenging role.
Work Experience
- Company X (2020-2024): built REST APIs with FastAPI and PostgreSQL.
Education
- Bachelor of Computer Science, HUTECH University.
Skills: Python, FastAPI, Docker.
Projects: internal analytics platform.
Certifications: AWS Certified.
"""

JD_SAMPLE = """
Job Description: Senior Backend Engineer
We are looking for a backend engineer to join our team.
Responsibilities:
- You will be responsible for designing REST APIs.
- Maintain PostgreSQL databases.
Requirements:
- Must have 3+ years with Python and FastAPI.
Nice to have: Docker, AWS.
Benefits: competitive salary, health insurance.
Location: Ho Chi Minh City.
Apply now.
"""

CV_SAMPLE_VI = """
Sơ yếu lý lịch
Họ tên: Trần Thị B
Email: btran@example.com — Điện thoại: 0987 654 321
Mục tiêu nghề nghiệp: trở thành lập trình viên backend.
Kinh nghiệm làm việc: 3 năm tại công ty phần mềm.
Học vấn: Cử nhân Công nghệ thông tin, trường đại học Bách Khoa.
Kỹ năng: Python, SQL. Dự án: hệ thống quản lý.
"""

JD_SAMPLE_VI = """
Mô tả công việc: Kỹ sư Backend
Chúng tôi đang tìm kiếm một kỹ sư backend.
Trách nhiệm: xây dựng API và bảo trì cơ sở dữ liệu.
Yêu cầu công việc: bắt buộc có 3 năm kinh nghiệm Python.
Quyền lợi: mức lương cạnh tranh, phúc lợi đầy đủ.
Địa điểm làm việc: Hà Nội.
"""


def test_detect_cv_english():
    result = detect_document_type(CV_SAMPLE)
    assert result["detected_type"] == "cv"
    assert result["cv_score"] > result["jd_score"]


def test_detect_jd_english():
    result = detect_document_type(JD_SAMPLE)
    assert result["detected_type"] == "jd"
    assert result["jd_score"] > result["cv_score"]


def test_detect_cv_vietnamese():
    result = detect_document_type(CV_SAMPLE_VI)
    assert result["detected_type"] == "cv"


def test_detect_jd_vietnamese():
    result = detect_document_type(JD_SAMPLE_VI)
    assert result["detected_type"] == "jd"


def test_validate_mismatch_jd_in_cv_slot():
    # Người dùng bỏ JD vào ô CV -> phải báo mismatch.
    result = validate_expected_type(JD_SAMPLE, "cv")
    assert result["validation_status"] == "mismatch"
    assert result["detected_type"] == "jd"


def test_validate_mismatch_cv_in_jd_slot():
    result = validate_expected_type(CV_SAMPLE, "jd")
    assert result["validation_status"] == "mismatch"
    assert result["detected_type"] == "cv"


def test_validate_valid_cv():
    result = validate_expected_type(CV_SAMPLE, "cv")
    assert result["validation_status"] == "valid"


def test_validate_valid_jd():
    result = validate_expected_type(JD_SAMPLE, "jd")
    assert result["validation_status"] == "valid"


def test_ambiguous_short_text_is_unknown_not_blocked():
    # Văn bản quá ngắn / mơ hồ -> unknown (cho qua), không được coi là mismatch.
    result = validate_expected_type("Xin chào, đây là một tài liệu.", "cv")
    assert result["validation_status"] in ("unknown", "valid")
    assert result["validation_status"] != "mismatch"


# --- Gốc bug: text tiếng Việt MẤT DẤU (OCR/parser) vẫn phải nhận đúng loại ---

CV_NO_DIACRITIC = """
Nguyen Van A - Backend Developer
Kinh nghiem: 2 nam lam viec tai cong ty X
Hoc van: Dai hoc Bach Khoa. Ky nang: Python, FastAPI, Docker.
Du an: he thong quan ly. Chung chi: AWS.
"""

JD_NO_DIACRITIC = """
Tuyen Backend Engineer
Mo ta cong viec: xay dung va bao tri API.
Yeu cau cong viec: 3 nam kinh nghiem Python.
Trach nhiem: thiet ke he thong. Quyen loi: luong thuong hap dan.
"""


def test_detect_cv_vietnamese_no_diacritic():
    """CV tiếng Việt không dấu (OCR) trước đây bị 'unknown' -> giờ phải là cv."""
    result = detect_document_type(CV_NO_DIACRITIC)
    assert result["detected_type"] == "cv"


def test_detect_jd_vietnamese_no_diacritic():
    result = detect_document_type(JD_NO_DIACRITIC)
    assert result["detected_type"] == "jd"


def test_block_jd_in_cv_slot_no_diacritic():
    """Chính lỗi người dùng gặp: JD không dấu bỏ vào ô CV phải bị chặn."""
    assert validate_expected_type(JD_NO_DIACRITIC, "cv")["validation_status"] == "mismatch"


def test_block_cv_in_jd_slot_no_diacritic():
    assert validate_expected_type(CV_NO_DIACRITIC, "jd")["validation_status"] == "mismatch"


def test_valid_no_diacritic():
    assert validate_expected_type(CV_NO_DIACRITIC, "cv")["validation_status"] == "valid"
    assert validate_expected_type(JD_NO_DIACRITIC, "jd")["validation_status"] == "valid"


def test_ocr_noisy_jd_still_detected():
    """Text OCR vỡ chữ vẫn nhận ra JD nhờ các từ khóa còn nguyên."""
    ocr = ("Corporate IT Job Description. Responsibties for corporate. "
           "Define governance standards. qualifications and requirements.")
    assert detect_document_type(ocr)["detected_type"] == "jd"


def test_strip_accents_helper():
    from app.services.document_classifier import strip_accents
    assert strip_accents("Kinh nghiệm") == "kinh nghiem"
    assert strip_accents("Đại học") == "dai hoc"
