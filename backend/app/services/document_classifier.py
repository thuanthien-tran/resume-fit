"""PhÃƒÆ’Ã‚Â¢n loÃƒÂ¡Ã‚ÂºÃ‚Â¡i tÃƒÆ’Ã‚Â i liÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¡u CV / JD dÃƒÂ¡Ã‚Â»Ã‚Â±a trÃƒÆ’Ã‚Âªn nÃƒÂ¡Ã‚Â»Ã¢â€žÂ¢i dung (rule-based, song ngÃƒÂ¡Ã‚Â»Ã‚Â¯ Anh/ViÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¡t).

DÃƒÆ’Ã‚Â¹ng Ãƒâ€žÃ¢â‚¬ËœÃƒÂ¡Ã‚Â»Ã†â€™ xÃƒÆ’Ã‚Â¡c minh ngÃƒâ€ Ã‚Â°ÃƒÂ¡Ã‚Â»Ã‚Âi dÃƒÆ’Ã‚Â¹ng cÃƒÆ’Ã‚Â³ tÃƒÂ¡Ã‚ÂºÃ‚Â£i Ãƒâ€žÃ¢â‚¬ËœÃƒÆ’Ã‚Âºng loÃƒÂ¡Ã‚ÂºÃ‚Â¡i tÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¡p vÃƒÆ’Ã‚Â o Ãƒâ€žÃ¢â‚¬ËœÃƒÆ’Ã‚Âºng ÃƒÆ’Ã‚Â´ hay khÃƒÆ’Ã‚Â´ng, trÃƒÆ’Ã‚Â¡nh
lÃƒÂ¡Ã‚Â»Ã¢â‚¬â€i Ãƒâ€žÃ¢â‚¬ËœÃƒÂ¡Ã‚ÂºÃ‚Â£o ngÃƒâ€ Ã‚Â°ÃƒÂ¡Ã‚Â»Ã‚Â£c CV/JD khiÃƒÂ¡Ã‚ÂºÃ‚Â¿n matching engine chÃƒÂ¡Ã‚ÂºÃ‚Â¥m Ãƒâ€žÃ¢â‚¬ËœiÃƒÂ¡Ã‚Â»Ã†â€™m sai.

Text trÃƒÆ’Ã‚Â­ch xuÃƒÂ¡Ã‚ÂºÃ‚Â¥t thÃƒÂ¡Ã‚Â»Ã‚Â±c tÃƒÂ¡Ã‚ÂºÃ‚Â¿ (OCR/PDF) thÃƒâ€ Ã‚Â°ÃƒÂ¡Ã‚Â»Ã‚Âng MÃƒÂ¡Ã‚ÂºÃ‚Â¤T DÃƒÂ¡Ã‚ÂºÃ‚Â¤U tiÃƒÂ¡Ã‚ÂºÃ‚Â¿ng ViÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¡t hoÃƒÂ¡Ã‚ÂºÃ‚Â·c sai chÃƒÆ’Ã‚Â­nh tÃƒÂ¡Ã‚ÂºÃ‚Â£,
nÃƒÆ’Ã‚Âªn toÃƒÆ’Ã‚Â n bÃƒÂ¡Ã‚Â»Ã¢â€žÂ¢ so khÃƒÂ¡Ã‚Â»Ã¢â‚¬Âºp Ãƒâ€žÃ¢â‚¬ËœÃƒâ€ Ã‚Â°ÃƒÂ¡Ã‚Â»Ã‚Â£c thÃƒÂ¡Ã‚Â»Ã‚Â±c hiÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¡n trÃƒÆ’Ã‚Âªn vÃƒâ€žÃ†â€™n bÃƒÂ¡Ã‚ÂºÃ‚Â£n Ãƒâ€žÃ¢â‚¬ËœÃƒÆ’Ã‚Â£ bÃƒÂ¡Ã‚Â»Ã‚Â dÃƒÂ¡Ã‚ÂºÃ‚Â¥u Ãƒâ€žÃ¢â‚¬ËœÃƒÂ¡Ã‚Â»Ã†â€™ bÃƒÂ¡Ã‚ÂºÃ‚Â¯t Ãƒâ€žÃ¢â‚¬ËœÃƒâ€ Ã‚Â°ÃƒÂ¡Ã‚Â»Ã‚Â£c nhiÃƒÂ¡Ã‚Â»Ã‚Âu
biÃƒÂ¡Ã‚ÂºÃ‚Â¿n thÃƒÂ¡Ã‚Â»Ã†â€™ hÃƒâ€ Ã‚Â¡n ("kinh nghiem" vÃƒÂ¡Ã‚ÂºÃ‚Â«n khÃƒÂ¡Ã‚Â»Ã¢â‚¬Âºp "kinh nghiÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¡m").
"""
import re
import unicodedata
from typing import Literal

DocumentType = Literal["cv", "jd", "unknown"]


def collapse_letter_spaced_text(text: str) -> str:
    """Normalize PDF text extracted with spaces between every character.

    Some CV templates export text like ``K i n h  n g h i Ã¡Â»â€¡ m``. Keyword
    matching then misses strong CV signals and the upload is rejected as
    unknown/mismatch. Collapse single inter-character spaces only on lines that
    are clearly letter-spaced, while preserving double-space word boundaries.
    """
    fixed_lines: list[str] = []
    for line in (text or "").splitlines():
        tokens = re.findall(r"\S+", line)
        if not tokens:
            fixed_lines.append(line)
            continue
        single_char_tokens = [token for token in tokens if len(token) == 1 and token.isalnum()]
        letter_spaced = len(single_char_tokens) >= 4 and len(single_char_tokens) / max(len(tokens), 1) >= 0.55
        if not letter_spaced:
            fixed_lines.append(line)
            continue

        collapsed = re.sub(r"(?<=\w) (?=\w)", "", line)
        collapsed = re.sub(r"\s*([@._+\-/])\s*", r"\1", collapsed)
        collapsed = re.sub(r" {2,}", " ", collapsed)
        fixed_lines.append(collapsed.strip())
    return "\n".join(fixed_lines)


def strip_accents(text: str) -> str:
    """BÃƒÂ¡Ã‚Â»Ã‚Â dÃƒÂ¡Ã‚ÂºÃ‚Â¥u tiÃƒÂ¡Ã‚ÂºÃ‚Â¿ng ViÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¡t vÃƒÆ’Ã‚Â  hÃƒÂ¡Ã‚ÂºÃ‚Â¡ vÃƒÂ¡Ã‚Â»Ã‚Â chÃƒÂ¡Ã‚Â»Ã‚Â¯ thÃƒâ€ Ã‚Â°ÃƒÂ¡Ã‚Â»Ã‚Âng Ãƒâ€žÃ¢â‚¬ËœÃƒÂ¡Ã‚Â»Ã†â€™ so khÃƒÂ¡Ã‚Â»Ã¢â‚¬Âºp bÃƒÂ¡Ã‚Â»Ã‚Ân vÃƒÂ¡Ã‚Â»Ã¢â‚¬Âºi OCR/parser."""
    text = collapse_letter_spaced_text(text)
    text = text.replace(chr(0x0111), "d").replace(chr(0x0110), "D")
    decomposed = unicodedata.normalize("NFD", text)
    without = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return without.lower()


# TÃƒÂ¡Ã‚Â»Ã‚Â« khÃƒÆ’Ã‚Â³a CV (viÃƒÂ¡Ã‚ÂºÃ‚Â¿t KHÃƒÆ’Ã¢â‚¬ÂNG dÃƒÂ¡Ã‚ÂºÃ‚Â¥u vÃƒÆ’Ã‚Â¬ text so khÃƒÂ¡Ã‚Â»Ã¢â‚¬Âºp Ãƒâ€žÃ¢â‚¬ËœÃƒÆ’Ã‚Â£ Ãƒâ€žÃ¢â‚¬ËœÃƒâ€ Ã‚Â°ÃƒÂ¡Ã‚Â»Ã‚Â£c bÃƒÂ¡Ã‚Â»Ã‚Â dÃƒÂ¡Ã‚ÂºÃ‚Â¥u). (tÃƒÂ¡Ã‚Â»Ã‚Â«_khÃƒÆ’Ã‚Â³a, Ãƒâ€žÃ¢â‚¬ËœiÃƒÂ¡Ã‚Â»Ã†â€™m)
CV_KEYWORDS: list[tuple[str, int]] = [
    ("work experience", 3), ("professional experience", 3),
    ("employment history", 3), ("work history", 3), ("education", 2),
    ("skills", 2), ("projects", 2), ("certifications", 2), ("certificate", 2),
    ("summary", 1), ("profile", 1), ("objective", 2), ("career objective", 3),
    ("references", 1), ("university", 2), ("bachelor", 2), ("master", 2),
    ("linkedin", 3), ("github", 3), ("portfolio", 2), ("curriculum vitae", 4),
    ("resume", 3), ("date of birth", 2), ("hobbies", 1), ("achievements", 1),
    # TiÃƒÂ¡Ã‚ÂºÃ‚Â¿ng ViÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¡t (Ãƒâ€žÃ¢â‚¬ËœÃƒÆ’Ã‚Â£ bÃƒÂ¡Ã‚Â»Ã‚Â dÃƒÂ¡Ã‚ÂºÃ‚Â¥u)
    ("kinh nghiem lam viec", 3), ("kinh nghiem", 2), ("hoc van", 2),
    ("trinh do hoc van", 3), ("ky nang", 2), ("du an", 2), ("chung chi", 2),
    ("muc tieu nghe nghiep", 3), ("thong tin ca nhan", 3),
    ("qua trinh lam viec", 3), ("truong dai hoc", 2), ("cu nhan", 2),
    ("thac si", 2), ("so yeu ly lich", 4), ("ngay sinh", 2),
    ("so dien thoai", 2), ("dia chi", 1), ("gioi thieu ban than", 3),
]

# TÃƒÂ¡Ã‚Â»Ã‚Â« khÃƒÆ’Ã‚Â³a JD (khÃƒÆ’Ã‚Â´ng dÃƒÂ¡Ã‚ÂºÃ‚Â¥u).
JD_KEYWORDS: list[tuple[str, int]] = [
    ("job description", 4), ("responsibilities", 3), ("responsibility", 2),
    ("requirements", 3), ("qualifications", 3), ("must have", 2),
    ("must-have", 2), ("nice to have", 2), ("nice-to-have", 2),
    ("benefits", 2), ("salary", 2), ("job title", 3), ("we are looking for", 3),
    ("we are hiring", 3), ("you will be responsible", 3), ("the candidate will", 3),
    ("apply now", 2), ("job type", 2), ("employment type", 2), ("reporting to", 2),
    ("what you'll do", 3), ("who you are", 2), ("about the role", 3),
    ("about the job", 3), ("key responsibilities", 4), ("job summary", 3),
    # TiÃƒÂ¡Ã‚ÂºÃ‚Â¿ng ViÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¡t (Ãƒâ€žÃ¢â‚¬ËœÃƒÆ’Ã‚Â£ bÃƒÂ¡Ã‚Â»Ã‚Â dÃƒÂ¡Ã‚ÂºÃ‚Â¥u)
    ("mo ta cong viec", 4), ("yeu cau cong viec", 4), ("trach nhiem", 2),
    ("quyen loi", 2), ("phuc loi", 2), ("muc luong", 2),
    ("dia diem lam viec", 3), ("ung vien can", 3),
    ("chung toi dang tim kiem", 3), ("nhiem vu chinh", 3),
    ("yeu cau bat buoc", 3), ("quyen loi duoc huong", 3),
    ("mo ta chi tiet cong viec", 4), ("tuyen dung", 2), ("vi tri tuyen", 3),
    ("yeu cau ung vien", 3), ("mo ta", 1),
]

# Ãƒâ€žÃ‚ÂiÃƒÂ¡Ã‚Â»Ã†â€™m chÃƒÆ’Ã‚Âªnh tÃƒÂ¡Ã‚Â»Ã¢â‚¬Ëœi thiÃƒÂ¡Ã‚Â»Ã†â€™u Ãƒâ€žÃ¢â‚¬ËœÃƒÂ¡Ã‚Â»Ã†â€™ coi lÃƒÆ’Ã‚Â  CHÃƒÂ¡Ã‚ÂºÃ‚Â®C CHÃƒÂ¡Ã‚ÂºÃ‚Â®N mÃƒÂ¡Ã‚Â»Ã¢â€žÂ¢t loÃƒÂ¡Ã‚ÂºÃ‚Â¡i (dÃƒâ€ Ã‚Â°ÃƒÂ¡Ã‚Â»Ã¢â‚¬Âºi ngÃƒâ€ Ã‚Â°ÃƒÂ¡Ã‚Â»Ã‚Â¡ng -> unknown).
_MARGIN = 3

# Minimum evidence required before accepting a file as the selected slot type.
# This prevents arbitrary documents that contain one or two generic words ("skills",
# "requirements", "salary"...) from being accepted as CV/JD.
_MIN_VALID_SCORE = {"cv": 7, "jd": 8}
_MIN_VALID_MARGIN = 2

# Strong structural signals. These are scored separately from generic keywords so
# a real CV/JD can be accepted even when formatting/language is unusual, while a
# random report/proposal with a few tech keywords is rejected as unknown.
CV_SECTION_PATTERNS: list[tuple[str, int]] = [
    (r"\b(work|professional|employment)\s+(experience|history)\b", 4),
    (r"\b(education|academic background)\b", 2),
    (r"\b(skills|technical skills|core competencies)\b", 2),
    (r"\b(projects?|certifications?|awards?)\b", 2),
    (r"\b(kinh nghiem lam viec|qua trinh lam viec|hoc van|ky nang|du an|chung chi)\b", 3),
    (r"\b(thong tin ca nhan|muc tieu nghe nghiep|so yeu ly lich)\b", 4),
]

JD_SECTION_PATTERNS: list[tuple[str, int]] = [
    (r"\b(job description|job summary|about the role|about the job)\b", 5),
    (r"\b(key\s+)?responsibilit(y|ies)\b", 4),
    (r"\b(requirements?|qualifications?|candidate profile)\b", 4),
    (r"\b(benefits?|compensation|salary|employment type|job type|location)\b", 2),
    (r"\b(mo ta cong viec|yeu cau cong viec|yeu cau ung vien|nhiem vu chinh)\b", 5),
    (r"\b(quyen loi|phuc loi|muc luong|dia diem lam viec|vi tri tuyen)\b", 3),
]

OTHER_DOCUMENT_PATTERNS: list[tuple[str, int]] = [
    (r"\b(invoice|receipt|purchase order|quotation|tax code|amount due)\b", 5),
    (r"\b(contract|agreement|party a|party b|terms and conditions)\b", 4),
    (r"\b(meeting minutes|minutes of meeting|agenda|attendees|action items)\b", 4),
    (r"\b(report|proposal|business plan|market analysis|financial statement)\b", 3),
    (r"\b(syllabus|lesson plan|assignment|exam|transcript)\b", 4),
    (r"\b(hoa don|bien nhan|hop dong|bien ban|bao cao|de xuat|giao trinh)\b", 4),
]

def _count_keyword(text: str, keyword: str) -> bool:
    """KhÃƒÂ¡Ã‚Â»Ã¢â‚¬Âºp theo ranh giÃƒÂ¡Ã‚Â»Ã¢â‚¬Âºi tÃƒÂ¡Ã‚Â»Ã‚Â« Ãƒâ€žÃ¢â‚¬ËœÃƒÂ¡Ã‚Â»Ã†â€™ 'skills' khÃƒÆ’Ã‚Â´ng dÃƒÆ’Ã‚Â­nh 'reskills'."""
    pattern = rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def _count_regex(text: str, pattern: str) -> bool:
    return re.search(pattern, text) is not None


def _count_matches(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text))


def detect_document_type(text: str) -> dict:
    """PhÃƒÆ’Ã‚Â¢n loÃƒÂ¡Ã‚ÂºÃ‚Â¡i mÃƒÂ¡Ã‚Â»Ã¢â€žÂ¢t Ãƒâ€žÃ¢â‚¬ËœoÃƒÂ¡Ã‚ÂºÃ‚Â¡n vÃƒâ€žÃ†â€™n bÃƒÂ¡Ã‚ÂºÃ‚Â£n lÃƒÆ’Ã‚Â  CV, JD hay unknown.

    TrÃƒÂ¡Ã‚ÂºÃ‚Â£ vÃƒÂ¡Ã‚Â»Ã‚Â dict gÃƒÂ¡Ã‚Â»Ã¢â‚¬Å“m detected_type, confidence, cv_score, jd_score, reasons.
    """
    raw = text or ""
    normalized = strip_accents(raw)  # bÃƒÂ¡Ã‚Â»Ã‚Â dÃƒÂ¡Ã‚ÂºÃ‚Â¥u + thÃƒâ€ Ã‚Â°ÃƒÂ¡Ã‚Â»Ã‚Âng hÃƒÆ’Ã‚Â³a
    cv_score = 0
    jd_score = 0
    other_score = 0
    reasons: list[str] = []

    for keyword, weight in CV_KEYWORDS:
        if _count_keyword(normalized, keyword):
            cv_score += weight
            reasons.append(f"CV keyword: {keyword}")

    for keyword, weight in JD_KEYWORDS:
        if _count_keyword(normalized, keyword):
            jd_score += weight
            reasons.append(f"JD keyword: {keyword}")

    for pattern, weight in CV_SECTION_PATTERNS:
        if _count_regex(normalized, pattern):
            cv_score += weight
            reasons.append(f"CV structure: {pattern}")

    for pattern, weight in JD_SECTION_PATTERNS:
        if _count_regex(normalized, pattern):
            jd_score += weight
            reasons.append(f"JD structure: {pattern}")

    for pattern, weight in OTHER_DOCUMENT_PATTERNS:
        if _count_regex(normalized, pattern):
            other_score += weight
            reasons.append(f"Other document signal: {pattern}")

    # Email + phone are strong CV signals only when they look like candidate contact
    # info. A JD may contain one HR email, so single email alone is not enough.
    emails = re.findall(r"[\w.\-]+@[\w.\-]+\.\w{2,}", raw)
    if emails:
        cv_score += 3
        reasons.append("CV signal: email/contact")
        if len(set(e.lower() for e in emails)) >= 2:
            cv_score += 3
            reasons.append("CV signal: multiple candidate emails")

    phone_matches = re.findall(r"(?:\+?\d[\s.\-]?){9,12}", raw)
    digits_only = re.sub(r"\D", "", raw)
    if phone_matches and 9 <= len(digits_only) <= 80:
        cv_score += 2
        reasons.append("CV signal: phone/contact")
        if len(phone_matches) >= 2:
            cv_score += 2
            reasons.append("CV signal: multiple phone numbers")

    # Repeated complete anchors are a good sign that the user pasted many documents
    # of the same type into one slot. We still classify the dominant type so the
    # opposite slot can be blocked reliably.
    repeated_cv_sections = sum(_count_matches(normalized, p) for p, _ in CV_SECTION_PATTERNS)
    repeated_jd_sections = sum(_count_matches(normalized, p) for p, _ in JD_SECTION_PATTERNS)
    if repeated_cv_sections >= 4 or len(set(e.lower() for e in emails)) >= 2:
        cv_score += 4
        reasons.append("CV signal: repeated CV sections / multiple CVs")
    if repeated_jd_sections >= 4 or _count_matches(normalized, r"\bjob description\b|\bmo ta cong viec\b") >= 2:
        jd_score += 4
        reasons.append("JD signal: repeated JD sections / multiple JDs")

    # Company/recruiting voice is characteristic of JD, not CV.
    jd_voice_patterns = [
        r"\bwe are (looking for|hiring|seeking)\b",
        r"\byou will (be responsible|work|join|own|lead)\b",
        r"\bthe (successful )?candidate (will|must|should)\b",
        r"\bapply (now|today)|send your cv|submit your application\b",
        r"\b(chung toi dang tim kiem|ung vien se|nop ho so|gui cv)\b",
    ]
    for pattern in jd_voice_patterns:
        if _count_regex(normalized, pattern):
            jd_score += 3
            reasons.append(f"JD voice: {pattern}")

    # Penalize generic/non-HR documents when they lack enough CV/JD evidence.
    if other_score >= 4 and max(cv_score, jd_score) < 12:
        cv_score = max(0, cv_score - 3)
        jd_score = max(0, jd_score - 3)

    total = max(cv_score + jd_score + other_score, 1)
    diff = abs(cv_score - jd_score)
    confidence = round(diff / total * 100, 2)

    if cv_score >= jd_score + _MARGIN and cv_score >= _MIN_VALID_SCORE["cv"] and cv_score > other_score:
        detected_type: DocumentType = "cv"
    elif jd_score >= cv_score + _MARGIN and jd_score >= _MIN_VALID_SCORE["jd"] and jd_score > other_score:
        detected_type = "jd"
    else:
        detected_type = "unknown"

    return {
        "detected_type": detected_type,
        "confidence": confidence,
        "cv_score": cv_score,
        "jd_score": jd_score,
        "other_score": other_score,
        "reasons": reasons[:12],
    }

def validate_expected_type(text: str, expected_type: str) -> dict:
    """So sÃƒÆ’Ã‚Â¡nh loÃƒÂ¡Ã‚ÂºÃ‚Â¡i phÃƒÆ’Ã‚Â¡t hiÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¡n vÃƒÂ¡Ã‚Â»Ã¢â‚¬Âºi loÃƒÂ¡Ã‚ÂºÃ‚Â¡i kÃƒÂ¡Ã‚Â»Ã‚Â³ vÃƒÂ¡Ã‚Â»Ã‚Âng (ÃƒÆ’Ã‚Â´ ngÃƒâ€ Ã‚Â°ÃƒÂ¡Ã‚Â»Ã‚Âi dÃƒÆ’Ã‚Â¹ng chÃƒÂ¡Ã‚Â»Ã‚Ân).

    validation_status:
      - valid:    Ãƒâ€žÃ¢â‚¬ËœÃƒÂ¡Ã‚Â»Ã‚Â§ bÃƒÂ¡Ã‚ÂºÃ‚Â±ng chÃƒÂ¡Ã‚Â»Ã‚Â©ng vÃƒÆ’Ã‚Â  khÃƒÂ¡Ã‚Â»Ã¢â‚¬Âºp Ãƒâ€žÃ¢â‚¬ËœÃƒÆ’Ã‚Âºng loÃƒÂ¡Ã‚ÂºÃ‚Â¡i kÃƒÂ¡Ã‚Â»Ã‚Â³ vÃƒÂ¡Ã‚Â»Ã‚Âng
      - mismatch: Ãƒâ€žÃ¢â‚¬ËœÃƒÂ¡Ã‚Â»Ã‚Â§ bÃƒÂ¡Ã‚ÂºÃ‚Â±ng chÃƒÂ¡Ã‚Â»Ã‚Â©ng nghiÃƒÆ’Ã‚Âªng rÃƒÆ’Ã‚Âµ vÃƒÂ¡Ã‚Â»Ã‚Â loÃƒÂ¡Ã‚ÂºÃ‚Â¡i ngÃƒâ€ Ã‚Â°ÃƒÂ¡Ã‚Â»Ã‚Â£c lÃƒÂ¡Ã‚ÂºÃ‚Â¡i
      - unknown:  khÃƒÆ’Ã‚Â´ng Ãƒâ€žÃ¢â‚¬ËœÃƒÂ¡Ã‚Â»Ã‚Â§ bÃƒÂ¡Ã‚ÂºÃ‚Â±ng chÃƒÂ¡Ã‚Â»Ã‚Â©ng lÃƒÆ’Ã‚Â  CV/JD, hoÃƒÂ¡Ã‚ÂºÃ‚Â·c tÃƒÆ’Ã‚Â i liÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¡u khÃƒÆ’Ã‚Â¡c/pha trÃƒÂ¡Ã‚Â»Ã¢â€žÂ¢n mÃƒâ€ Ã‚Â¡ hÃƒÂ¡Ã‚Â»Ã¢â‚¬Å“

    Upload/worker nÃƒÆ’Ã‚Âªn chÃƒÂ¡Ã‚Â»Ã¢â‚¬Â° cho qua status "valid". "unknown" khÃƒÆ’Ã‚Â´ng phÃƒÂ¡Ã‚ÂºÃ‚Â£i mismatch
    ngÃƒâ€ Ã‚Â°ÃƒÂ¡Ã‚Â»Ã‚Â£c loÃƒÂ¡Ã‚ÂºÃ‚Â¡i, nhÃƒâ€ Ã‚Â°ng vÃƒÂ¡Ã‚ÂºÃ‚Â«n khÃƒÆ’Ã‚Â´ng an toÃƒÆ’Ã‚Â n Ãƒâ€žÃ¢â‚¬ËœÃƒÂ¡Ã‚Â»Ã†â€™ phÃƒÆ’Ã‚Â¢n tÃƒÆ’Ã‚Â­ch CV-JD.
    """
    result = detect_document_type(text)
    cv, jd = result["cv_score"], result["jd_score"]

    if expected_type == "cv":
        right, wrong = cv, jd
        min_score = _MIN_VALID_SCORE["cv"]
        opposite = "jd"
    else:
        right, wrong = jd, cv
        min_score = _MIN_VALID_SCORE["jd"]
        opposite = "cv"

    if result["detected_type"] == expected_type and right >= min_score and right >= wrong + _MIN_VALID_MARGIN:
        status = "valid"
    elif result["detected_type"] == opposite or wrong >= right + _MARGIN and wrong >= _MIN_VALID_SCORE[opposite]:
        status = "mismatch"
    else:
        status = "unknown"

    result["expected_type"] = expected_type
    result["validation_status"] = status
    return result