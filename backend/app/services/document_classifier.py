"""Phân loại tài liệu CV / JD dựa trên nội dung (rule-based, song ngữ Anh/Việt).

Dùng để xác minh người dùng có tải đúng loại tệp vào đúng ô hay không, tránh
lỗi đảo ngược CV/JD khiến matching engine chấm điểm sai.

Text trích xuất thực tế (OCR/PDF) thường MẤT DẤU tiếng Việt hoặc sai chính tả,
nên toàn bộ so khớp được thực hiện trên văn bản đã bỏ dấu để bắt được nhiều
biến thể hơn ("kinh nghiem" vẫn khớp "kinh nghiệm").
"""
import re
import unicodedata
from typing import Literal

DocumentType = Literal["cv", "jd", "unknown"]


def strip_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt và hạ về chữ thường để so khớp bền với OCR/parser."""
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    without = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return without.lower()


# Từ khóa CV (viết KHÔNG dấu vì text so khớp đã được bỏ dấu). (từ_khóa, điểm)
CV_KEYWORDS: list[tuple[str, int]] = [
    ("work experience", 3), ("professional experience", 3),
    ("employment history", 3), ("work history", 3), ("education", 2),
    ("skills", 2), ("projects", 2), ("certifications", 2), ("certificate", 2),
    ("summary", 1), ("profile", 1), ("objective", 2), ("career objective", 3),
    ("references", 1), ("university", 2), ("bachelor", 2), ("master", 2),
    ("linkedin", 3), ("github", 3), ("portfolio", 2), ("curriculum vitae", 4),
    ("resume", 3), ("date of birth", 2), ("hobbies", 1), ("achievements", 1),
    # Tiếng Việt (đã bỏ dấu)
    ("kinh nghiem lam viec", 3), ("kinh nghiem", 2), ("hoc van", 2),
    ("trinh do hoc van", 3), ("ky nang", 2), ("du an", 2), ("chung chi", 2),
    ("muc tieu nghe nghiep", 3), ("thong tin ca nhan", 3),
    ("qua trinh lam viec", 3), ("truong dai hoc", 2), ("cu nhan", 2),
    ("thac si", 2), ("so yeu ly lich", 4), ("ngay sinh", 2),
    ("so dien thoai", 2), ("dia chi", 1), ("gioi thieu ban than", 3),
]

# Từ khóa JD (không dấu).
JD_KEYWORDS: list[tuple[str, int]] = [
    ("job description", 4), ("responsibilities", 3), ("responsibility", 2),
    ("requirements", 3), ("qualifications", 3), ("must have", 2),
    ("must-have", 2), ("nice to have", 2), ("nice-to-have", 2),
    ("benefits", 2), ("salary", 2), ("job title", 3), ("we are looking for", 3),
    ("we are hiring", 3), ("you will be responsible", 3), ("the candidate will", 3),
    ("apply now", 2), ("job type", 2), ("employment type", 2), ("reporting to", 2),
    ("what you'll do", 3), ("who you are", 2), ("about the role", 3),
    ("about the job", 3), ("key responsibilities", 4), ("job summary", 3),
    # Tiếng Việt (đã bỏ dấu)
    ("mo ta cong viec", 4), ("yeu cau cong viec", 4), ("trach nhiem", 2),
    ("quyen loi", 2), ("phuc loi", 2), ("muc luong", 2),
    ("dia diem lam viec", 3), ("ung vien can", 3),
    ("chung toi dang tim kiem", 3), ("nhiem vu chinh", 3),
    ("yeu cau bat buoc", 3), ("quyen loi duoc huong", 3),
    ("mo ta chi tiet cong viec", 4), ("tuyen dung", 2), ("vi tri tuyen", 3),
    ("yeu cau ung vien", 3), ("mo ta", 1),
]

# Điểm chênh tối thiểu để coi là CHẮC CHẮN một loại (dưới ngưỡng -> unknown).
_MARGIN = 3


def _count_keyword(text: str, keyword: str) -> bool:
    """Khớp theo ranh giới từ để 'skills' không dính 'reskills'."""
    pattern = rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def detect_document_type(text: str) -> dict:
    """Phân loại một đoạn văn bản là CV, JD hay unknown.

    Trả về dict gồm detected_type, confidence, cv_score, jd_score, reasons.
    """
    raw = text or ""
    normalized = strip_accents(raw)  # bỏ dấu + thường hóa
    cv_score = 0
    jd_score = 0
    reasons: list[str] = []

    for keyword, weight in CV_KEYWORDS:
        if _count_keyword(normalized, keyword):
            cv_score += weight
            reasons.append(f"CV signal: {keyword}")

    for keyword, weight in JD_KEYWORDS:
        if _count_keyword(normalized, keyword):
            jd_score += weight
            reasons.append(f"JD signal: {keyword}")

    # Email là tín hiệu rất mạnh của CV (JD hầu như không có email ứng viên).
    if re.search(r"[\w.\-]+@[\w.\-]+\.\w{2,}", raw):
        cv_score += 4
        reasons.append("CV signal: email")

    # Số điện thoại: chuỗi 9-12 chữ số liền/cách nhẹ. Loại trừ dải năm kiểu
    # "2020-2024" (chỉ 8 số qua dấu gạch) bằng cách yêu cầu >= 9 chữ số.
    digits_only = re.sub(r"\D", "", raw)
    if re.search(r"(?:\+?\d[\s.\-]?){9,12}", raw) and 9 <= len(digits_only):
        # tránh false positive khi cả trang chỉ toàn số (bảng biểu)
        if len(digits_only) <= 40:
            cv_score += 2
            reasons.append("CV signal: phone")

    total = max(cv_score + jd_score, 1)
    diff = abs(cv_score - jd_score)
    confidence = round(diff / total * 100, 2)

    if cv_score >= jd_score + _MARGIN:
        detected_type: DocumentType = "cv"
    elif jd_score >= cv_score + _MARGIN:
        detected_type = "jd"
    else:
        detected_type = "unknown"

    return {
        "detected_type": detected_type,
        "confidence": confidence,
        "cv_score": cv_score,
        "jd_score": jd_score,
        "reasons": reasons[:10],
    }


def validate_expected_type(text: str, expected_type: str) -> dict:
    """So sánh loại phát hiện với loại kỳ vọng (ô người dùng chọn).

    Trả về validation_status:
      - "valid":    khớp loại kỳ vọng, hoặc tín hiệu nghiêng đúng phía
      - "mismatch": tín hiệu nghiêng RÕ về loại NGƯỢC lại -> chặn
      - "unknown":  không đủ tín hiệu để kết luận -> cho qua (cảnh báo nhẹ)

    Khác bản cũ: dùng so sánh trực tiếp cv_score vs jd_score theo phía kỳ vọng,
    nên bắt được cả trường hợp điểm thấp nhưng lệch hẳn về loại sai.
    """
    result = detect_document_type(text)
    cv, jd = result["cv_score"], result["jd_score"]

    if expected_type == "cv":
        wrong, right = jd, cv
    else:
        wrong, right = cv, jd

    if wrong >= right + _MARGIN:
        status = "mismatch"      # nghiêng rõ về loại sai
    elif right >= wrong + _MARGIN or right > 0 and wrong == 0:
        status = "valid"         # nghiêng về loại đúng
    else:
        status = "unknown"       # mơ hồ

    result["expected_type"] = expected_type
    result["validation_status"] = status
    return result
