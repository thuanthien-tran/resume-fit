from __future__ import annotations

from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any


FONT_CANDIDATES = (
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
)


def _text(value: Any, fallback: str = "Không rõ") -> str:
    if value is None or value == "":
        return fallback
    return str(value)


def _percent(value: Any, fallback: str = "N/A") -> str:
    if value is None or value == "":
        return fallback
    return f"{value}%"


def _safe_paragraph(value: Any) -> str:
    return escape(_text(value, "")).replace("\n", "<br/>")


def _register_fonts(pdfmetrics: Any, TTFont: Any) -> tuple[str, str]:
    for regular_path, bold_path in FONT_CANDIDATES:
        regular = Path(regular_path)
        bold = Path(bold_path)
        if regular.exists():
            pdfmetrics.registerFont(TTFont("ReportFont", str(regular)))
            if bold.exists():
                pdfmetrics.registerFont(TTFont("ReportFont-Bold", str(bold)))
                pdfmetrics.registerFontFamily("ReportFont", normal="ReportFont", bold="ReportFont-Bold")
                return "ReportFont", "ReportFont-Bold"
            pdfmetrics.registerFontFamily("ReportFont", normal="ReportFont", bold="ReportFont")
            return "ReportFont", "ReportFont"
    return "Helvetica", "Helvetica-Bold"


def _add_section(story: list[Any], styles: dict[str, Any], label: str, title: str, Spacer: Any, Paragraph: Any) -> None:
    story.append(Spacer(1, 12))
    story.append(_paragraph(label, Paragraph, styles["section_label"]))
    story.append(_paragraph(title, Paragraph, styles["section_title"]))


def _heading(text: str, Paragraph: Any, style: Any) -> Any:
    return Paragraph(_safe_paragraph(text), style)


def _paragraph(text: Any, Paragraph: Any, style: Any) -> Any:
    return Paragraph(_safe_paragraph(text), style)


def _bullet_list(title: str, items: list[str] | None, story: list[Any], Paragraph: Any, Spacer: Any, styles: dict[str, Any]) -> None:
    story.append(_heading(title, Paragraph, styles["subheading"]))
    if not items:
        story.append(_paragraph("Chưa có dữ liệu.", Paragraph, styles["muted"]))
        return
    for item in items:
        story.append(_paragraph(f"• {item}", Paragraph, styles["body"]))
    story.append(Spacer(1, 4))


def _tag_line(title: str, items: list[str] | None, story: list[Any], Paragraph: Any, styles: dict[str, Any]) -> None:
    if not items:
        return
    story.append(Paragraph(f"<b>{escape(title)}:</b> {escape(', '.join(items))}", styles["body"]))


def _split_long_text(text: str, chunk_size: int = 1800) -> list[str]:
    if not text:
        return ["Không có dữ liệu."]
    chunks: list[str] = []
    current = ""
    for line in text.splitlines() or [text]:
        next_value = f"{current}\n{line}" if current else line
        if len(next_value) > chunk_size and current:
            chunks.append(current)
            current = line
        else:
            current = next_value
    if current:
        chunks.append(current)
    return chunks


def build_candidate_report_pdf(result: dict[str, Any], candidate_name: str | None = None) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise RuntimeError("Thiếu thư viện reportlab để tạo PDF. Hãy cài đặt requirements backend.") from exc

    font_name, bold_font = _register_fonts(pdfmetrics, TTFont)
    base_styles = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base_styles["Title"],
            fontName=bold_font,
            fontSize=20,
            leading=26,
            textColor=colors.HexColor("#7d2740"),
            alignment=TA_CENTER,
            spaceAfter=10,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base_styles["BodyText"],
            fontName=font_name,
            fontSize=10,
            leading=15,
            textColor=colors.HexColor("#4b5563"),
            alignment=TA_CENTER,
            spaceAfter=16,
        ),
        "section_label": ParagraphStyle(
            "SectionLabel",
            parent=base_styles["BodyText"],
            fontName=bold_font,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#9f344f"),
            spaceBefore=4,
            spaceAfter=2,
        ),
        "section_title": ParagraphStyle(
            "SectionTitle",
            parent=base_styles["Heading2"],
            fontName=bold_font,
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#111827"),
            spaceBefore=0,
            spaceAfter=8,
        ),
        "subheading": ParagraphStyle(
            "Subheading",
            parent=base_styles["Heading3"],
            fontName=bold_font,
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#374151"),
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "ReportBody",
            parent=base_styles["BodyText"],
            fontName=font_name,
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#111827"),
            spaceAfter=4,
        ),
        "muted": ParagraphStyle(
            "ReportMuted",
            parent=base_styles["BodyText"],
            fontName=font_name,
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#6b7280"),
            spaceAfter=4,
        ),
        "mono": ParagraphStyle(
            "ReportMono",
            parent=base_styles["BodyText"],
            fontName=font_name,
            fontSize=7.5,
            leading=11,
            textColor=colors.HexColor("#111827"),
            borderColor=colors.HexColor("#d1d5db"),
            borderWidth=0.5,
            borderPadding=6,
            backColor=colors.HexColor("#f9fafb"),
            spaceAfter=8,
        ),
    }

    compatibility = result.get("compatibility") or {}
    score_breakdown = result.get("score_breakdown") or {}
    skills = result.get("skills_analysis") or {}
    summary = result.get("candidate_summary") or {}
    recommendations = result.get("recommendations") or {}
    metadata = result.get("metadata") or {}
    extracted = result.get("extracted_text") or {}
    interview_questions = result.get("interview_questions") or []
    alternative_roles = result.get("alternative_roles") or []
    warnings = result.get("warnings") or []

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Báo cáo chi tiết ứng viên",
    )

    story: list[Any] = []
    story.append(_paragraph("Báo cáo chi tiết ứng viên", Paragraph, styles["title"]))
    subtitle = "Đánh giá độ phù hợp giữa CV ứng viên và mô tả công việc."
    if candidate_name:
        subtitle = f"Ứng viên: {escape(candidate_name)}<br/>{subtitle}"
    story.append(Paragraph(subtitle, styles["subtitle"]))

    score_table = Table(
        [
            [
                _paragraph("Điểm phù hợp", Paragraph, styles["muted"]),
                _paragraph("Mức đánh giá", Paragraph, styles["muted"]),
                _paragraph("Khuyến nghị", Paragraph, styles["muted"]),
                _paragraph("Độ tin cậy", Paragraph, styles["muted"]),
            ],
            [
                _paragraph(_percent(compatibility.get("overall_score")), Paragraph, styles["section_title"]),
                _paragraph(_text(compatibility.get("level"), "N/A"), Paragraph, styles["body"]),
                _paragraph(_text(compatibility.get("recommendation"), "N/A"), Paragraph, styles["body"]),
                _paragraph(f"{_text(metadata.get('confidence_level'))} ({round(float(compatibility.get('confidence') or 0) * 100)}%)", Paragraph, styles["body"]),
            ],
        ],
        colWidths=[34 * mm, 42 * mm, 54 * mm, 42 * mm],
    )
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fff1f4")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(score_table)

    _add_section(story, styles, "01. Tổng quan", "Tổng quan đánh giá", Spacer, Paragraph)
    if compatibility.get("message"):
        story.append(_paragraph(compatibility.get("message"), Paragraph, styles["body"]))
    if summary.get("summary"):
        story.append(_heading("Tóm tắt ứng viên", Paragraph, styles["subheading"]))
        story.append(_paragraph(summary.get("summary"), Paragraph, styles["body"]))
    _bullet_list("Điểm mạnh", summary.get("strengths") or [], story, Paragraph, Spacer, styles)
    _bullet_list("Điểm yếu", summary.get("weaknesses") or [], story, Paragraph, Spacer, styles)
    _bullet_list("Cảnh báo rủi ro", summary.get("risk_flags") or warnings, story, Paragraph, Spacer, styles)

    if score_breakdown:
        story.append(_heading("Điểm thành phần", Paragraph, styles["subheading"]))
        score_rows = [[_paragraph("Tiêu chí", Paragraph, styles["muted"]), _paragraph("Điểm", Paragraph, styles["muted"]), _paragraph("Mô tả", Paragraph, styles["muted"])]]
        for key, item in score_breakdown.items():
            score_rows.append([
                _paragraph(str(key).replace("_", " ").title(), Paragraph, styles["body"]),
                _paragraph(_percent(item.get("score")), Paragraph, styles["body"]),
                _paragraph(_text(item.get("description"), ""), Paragraph, styles["body"]),
            ])
        table = Table(score_rows, colWidths=[45 * mm, 24 * mm, 103 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f9fafb")),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#e5e7eb")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(table)

    _add_section(story, styles, "02. Kỹ năng", "Phân tích kỹ năng", Spacer, Paragraph)
    story.append(_paragraph(f"Mức độ khớp kỹ năng: {_percent(skills.get('skill_match_ratio'))}", Paragraph, styles["body"]))
    _tag_line("Kỹ năng bắt buộc đã có", skills.get("matched_must_have"), story, Paragraph, styles)
    _tag_line("Kỹ năng bắt buộc còn thiếu", skills.get("missing_must_have"), story, Paragraph, styles)
    _tag_line("Kỹ năng ưu tiên đã có", skills.get("matched_nice_to_have"), story, Paragraph, styles)
    _tag_line("Kỹ năng ưu tiên còn thiếu", skills.get("missing_nice_to_have"), story, Paragraph, styles)
    _tag_line("Tất cả kỹ năng khớp", skills.get("matched_skills"), story, Paragraph, styles)
    _tag_line("Tất cả kỹ năng còn thiếu", skills.get("missing_skills"), story, Paragraph, styles)
    _tag_line("Kỹ năng bổ sung", skills.get("extra_skills"), story, Paragraph, styles)

    _add_section(story, styles, "03. Kinh nghiệm", "Kinh nghiệm, cấp bậc và lĩnh vực", Spacer, Paragraph)
    meta_rows = [
        ["Số năm KN ứng viên", _text(metadata.get("candidate_years"))],
        ["Số năm KN yêu cầu", _text(metadata.get("required_years"))],
        ["Cấp bậc ứng viên", _text(metadata.get("cv_role_level"))],
        ["Cấp bậc JD", _text(metadata.get("jd_role_level"))],
        ["Khớp cấp bậc", _percent(metadata.get("role_match"))],
        ["Khớp lĩnh vực", _percent(metadata.get("domain_match"))],
    ]
    meta_table = Table(
        [[_paragraph(k, Paragraph, styles["muted"]), _paragraph(v, Paragraph, styles["body"])] for k, v in meta_rows],
        colWidths=[58 * mm, 114 * mm],
    )
    meta_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#e5e7eb")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f9fafb")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(meta_table)
    _tag_line("Lĩnh vực của ứng viên", metadata.get("cv_domains"), story, Paragraph, styles)
    _tag_line("Lĩnh vực của JD", metadata.get("jd_domains"), story, Paragraph, styles)

    _add_section(story, styles, "04. Khuyến nghị", "Khuyến nghị hành động", Spacer, Paragraph)
    _bullet_list("Dành cho nhà tuyển dụng", recommendations.get("for_recruiter") or [], story, Paragraph, Spacer, styles)
    _bullet_list("Dành cho ứng viên", recommendations.get("for_candidate") or [], story, Paragraph, Spacer, styles)
    _tag_line("Vị trí thay thế phù hợp", alternative_roles, story, Paragraph, styles)

    _add_section(story, styles, "05. Phỏng vấn", "Câu hỏi phỏng vấn đề xuất", Spacer, Paragraph)
    if interview_questions:
        for index, question in enumerate(interview_questions, start=1):
            story.append(_paragraph(f"{index}. {question}", Paragraph, styles["body"]))
    else:
        story.append(_paragraph("Chưa có câu hỏi phỏng vấn.", Paragraph, styles["muted"]))

    story.append(PageBreak())
    _add_section(story, styles, "06. Văn bản trích xuất", "Văn bản trích xuất", Spacer, Paragraph)
    story.append(_heading(f"Văn bản CV {'(đã cắt bớt)' if extracted.get('cv_truncated') else ''}", Paragraph, styles["subheading"]))
    for chunk in _split_long_text(extracted.get("cv") or "Không có văn bản CV được lưu."):
        story.append(_paragraph(chunk, Paragraph, styles["mono"]))
    story.append(_heading(f"Văn bản JD {'(đã cắt bớt)' if extracted.get('jd_truncated') else ''}", Paragraph, styles["subheading"]))
    for chunk in _split_long_text(extracted.get("jd") or "Không có văn bản JD được lưu."):
        story.append(_paragraph(chunk, Paragraph, styles["mono"]))

    story.append(Spacer(1, 10))
    story.append(_paragraph(
        f"AI: {_text(metadata.get('ai_provider'), 'N/A')} / {_text(metadata.get('ai_model'), 'N/A')} | "
        f"Thời gian xử lý: {_text(metadata.get('processing_time_seconds'), 'N/A')}s",
        Paragraph,
        styles["muted"],
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
