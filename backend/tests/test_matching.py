from app.matching.engine import calculate_matching, get_compatibility_level


def test_matching_engine_basic():
    cv = "Python FastAPI PostgreSQL Docker 3 years experience Bachelor"
    jd = "Need Python FastAPI PostgreSQL Redis Docker 2 years experience"
    result = calculate_matching(cv, jd)
    assert result["matching_score"] > 0
    assert "python" in result["matched_skills"]
    assert "redis" in result["missing_skills"]
    assert "compatibility" in result
    assert "score_breakdown" in result
    assert result["compatibility"]["level"] in [
        "Rất phù hợp", "Phù hợp tốt", "Phù hợp trung bình", "Phù hợp thấp", "Không phù hợp"
    ]


def test_score_breakdown_weights():
    cv = "Python FastAPI PostgreSQL Docker"
    jd = "Need Python FastAPI PostgreSQL Redis Docker AWS"
    result = calculate_matching(cv, jd)
    breakdown = result["score_breakdown"]
    total_weight = sum(item["weight"] for item in breakdown.values())
    assert total_weight == 100


def test_compatibility_levels():
    assert get_compatibility_level(90)["level"] == "Rất phù hợp"
    assert get_compatibility_level(75)["level"] == "Phù hợp tốt"
    assert get_compatibility_level(60)["level"] == "Phù hợp trung bình"
    assert get_compatibility_level(45)["level"] == "Phù hợp thấp"
    assert get_compatibility_level(30)["level"] == "Không phù hợp"


def test_detect_role_level_seniority():
    from app.matching.engine import detect_role_level

    # Generic titles no longer misclassify as intern/mid.
    assert detect_role_level("Junior Developer") == "junior"
    assert detect_role_level("Senior Software Engineer") == "senior"
    assert detect_role_level("Engineering Manager") == "manager"
    # Word-boundary aware: "leader"/"ahead" must not trigger lead/head.
    assert detect_role_level("A great team leader ahead of schedule") == "unknown"


def test_classify_jd_skills_same_line():
    """Must-have và nice-to-have trên cùng một dòng phải được tách đúng."""
    from app.matching.engine import classify_jd_skills, extract_skills

    jd = "Required: Python, FastAPI. Nice to have: Docker, AWS."
    jd_skills = extract_skills(jd)
    result = classify_jd_skills(jd, jd_skills)

    assert "python" in result["must_have"]
    assert "fastapi" in result["must_have"]
    assert "docker" in result["nice_to_have"]
    assert "aws" in result["nice_to_have"]
    # Docker/AWS không được lọt vào must-have.
    assert "docker" not in result["must_have"]
    assert "aws" not in result["must_have"]


def test_classify_jd_skills_multiline_sections():
    """Section nice-to-have kéo dài sang dòng sau cho tới khi gặp indicator mới."""
    from app.matching.engine import classify_jd_skills, extract_skills

    jd = (
        "Requirements:\n"
        "Python\n"
        "PostgreSQL\n"
        "Nice to have:\n"
        "Docker\n"
        "Kubernetes\n"
    )
    jd_skills = extract_skills(jd)
    result = classify_jd_skills(jd, jd_skills)

    assert "python" in result["must_have"]
    assert "postgresql" in result["must_have"]
    assert "docker" in result["nice_to_have"]
    assert "kubernetes" in result["nice_to_have"]


def test_classify_jd_skills_must_have_wins_conflict():
    """Skill xuất hiện ở cả hai vùng thì ưu tiên must-have."""
    from app.matching.engine import classify_jd_skills, extract_skills

    jd = "Required: Python. Nice to have: Python is a plus."
    jd_skills = extract_skills(jd)
    result = classify_jd_skills(jd, jd_skills)

    assert "python" in result["must_have"]
    assert "python" not in result["nice_to_have"]


def test_infer_domain_from_skills_backend():
    """JD chỉ liệt kê skill backend vẫn suy ra được domain web_development."""
    from app.matching.engine import detect_domains, extract_skills

    text = "Python FastAPI PostgreSQL Redis Docker"
    skills = extract_skills(text)
    domains = detect_domains(text, skills)
    assert "web_development" in domains


def test_marketing_cv_vs_marketing_jd():
    """Sau khi thêm taxonomy marketing, CV/JD marketing khớp phải có skill match."""
    cv = ("Digital Marketing specialist. SEO, SEM, Google Ads, Facebook Ads, "
          "content marketing, social media, 4 years experience.")
    jd = ("Marketing Manager. Required: SEO, SEM, content marketing, "
          "social media, Google Analytics. 3 years experience.")
    result = calculate_matching(cv, jd)
    assert result["skill_score"] > 0
    assert "seo" in result["matched_skills"]
    assert "marketing" in result["cv_domains"]
    assert "marketing" in result["jd_domains"]


def test_cross_domain_intern_vs_manager_low_score():
    """Intern an ninh mạng vs IT Manager khác domain -> điểm bị cap thấp."""
    cv = "Cybersecurity Intern. SIEM, Wireshark, Nmap, Wazuh."
    jd = ("IT Manager. SAP, ERP, Oracle, PL/SQL, vendor management, "
          "stakeholder management, 7+ years experience.")
    result = calculate_matching(cv, jd)
    assert result["matching_score"] <= 35


def test_experience_parser_variants():
    """Parser số năm bắt được các mẫu phổ biến, kể cả dải năm."""
    from app.matching.engine import extract_years_experience as y
    assert y("5 years of experience") == 5
    assert y("minimum 3 years") == 3
    assert y("over 7 years experience") == 7
    assert y("at least 4 years") == 4
    assert y("3+ years") == 3
    assert y("tối thiểu 5 năm") == 5
    assert y("2 năm kinh nghiệm") == 2
    # Dải năm là phương án cuối.
    assert y("Quá trình làm việc: 2020 - 2024") == 4
    assert y("hello world") is None


def test_keyword_score_vietnamese():
    """Keyword score phải tính được từ tiếng Việt có dấu (trước đây bị bỏ qua)."""
    from app.matching.engine import calculate_keyword_score
    score = calculate_keyword_score(
        "kinh nghiệm quản lý dự án phần mềm",
        "yêu cầu kinh nghiệm quản lý dự án",
    )
    assert score > 0


def test_role_level_inferred_from_context_in_matching():
    """CV không có title nhưng nhiều năm + tín hiệu quản lý -> detect manager."""
    cv = ("Managed stakeholders and vendor budget. 8 years of experience "
          "leading cross-functional teams.")
    jd = ("IT Manager. 7+ years experience. stakeholder management, "
          "vendor management, budget.")
    result = calculate_matching(cv, jd)
    assert result["cv_role_level"] == "manager"
    assert result["role_compatibility"] >= 70
