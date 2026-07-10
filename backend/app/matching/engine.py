import re
from datetime import datetime


SKILL_SYNONYMS = {
    "js": "javascript",
    "py": "python",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "fast api": "fastapi",
    "fast-api": "fastapi",
    "node.js": "nodejs",
    "node js": "nodejs",
    "c#": "csharp",
    "c sharp": "csharp",
    ".net": "dotnet",
    "asp.net": "dotnet",
    "vue.js": "vuejs",
    "vue js": "vuejs",
    "angular.js": "angular",
    "react.js": "react",
    "react js": "react",
    "spring boot": "spring",
    "pl/sql": "plsql",
    "pl sql": "plsql",
    "t-sql": "tsql",
    "ms sql": "mssql",
    "sql server": "mssql",
    "mongo db": "mongodb",
    "no sql": "nosql",
    "machine learning": "machine learning",
    "deep learning": "deep learning",
    "ci/cd": "ci/cd",
    "ci cd": "ci/cd",
    "rest api": "rest api",
    "restful api": "rest api",
    "restful": "rest api",
    "amazon web services": "aws",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "microsoft azure": "azure",
    "elk stack": "elk",
    "elastic stack": "elk",
    "elasticsearch": "elk",
}

KNOWN_SKILLS = {
    # Programming languages
    "python", "java", "javascript", "typescript", "csharp", "c/c++",
    "golang", "rust", "ruby", "php", "swift", "kotlin", "scala",
    "r", "matlab", "perl", "lua", "dart", "elixir", "haskell",
    # Web frameworks
    "fastapi", "django", "flask", "spring", "dotnet", "react",
    "angular", "vuejs", "nodejs", "express", "nextjs", "nuxtjs",
    "laravel", "rails", "sinatra", "gin", "fiber",
    # Databases
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "sqlite", "oracle", "mssql",
    "plsql", "tsql", "nosql", "mariadb", "couchdb",
    # DevOps & Cloud
    "docker", "kubernetes", "aws", "gcp", "azure", "terraform",
    "ansible", "jenkins", "gitlab", "github actions", "ci/cd",
    "linux", "nginx", "apache", "helm", "prometheus", "grafana",
    # Data & AI
    "machine learning", "deep learning", "nlp", "tensorflow",
    "pytorch", "scikit-learn", "pandas", "numpy", "spark",
    "hadoop", "airflow", "dbt", "tableau", "power bi",
    "random forest", "neural network", "computer vision",
    # Security
    "cybersecurity", "penetration testing", "siem", "wireshark",
    "wazuh", "nessus", "burp suite", "metasploit", "nmap",
    "owasp", "firewall", "ids", "ips", "soc", "threat detection",
    "log analysis", "vulnerability assessment", "incident response",
    "encryption", "ssl", "tls", "vpn", "network security",
    # Enterprise & Management
    "sap", "erp", "crm", "salesforce", "jira", "confluence",
    "sdlc", "agile", "scrum", "kanban", "waterfall",
    "project management", "itil", "devops",
    # General
    "git", "rest api", "graphql", "grpc", "microservices",
    "jwt", "oauth", "html", "css", "sass", "webpack",
    "sqlalchemy", "alembic", "celery", "rabbitmq", "kafka",
    "pytest", "junit", "selenium", "cypress",
    "s3", "sqs", "rds", "lambda", "ec2",
    "vmware", "virtualbox", "vagrant",
    # Marketing
    "seo", "sem", "google ads", "facebook ads", "content marketing",
    "social media", "branding", "email marketing", "copywriting",
    "market research", "influencer marketing", "google analytics",
    # Sales
    "lead generation", "account management", "business development",
    "negotiation", "cold calling", "b2b sales", "b2c sales",
    "pipeline management", "sales forecasting",
    # Human Resources
    "recruitment", "onboarding", "payroll", "compensation", "benefits",
    "performance management", "employee relations", "talent acquisition",
    "training", "hris",
    # Finance & Accounting
    "financial analysis", "accounting", "audit", "tax", "budgeting",
    "forecasting", "financial reporting", "bookkeeping", "quickbooks",
    "financial modeling", "risk management",
    # Real Estate
    "listing", "brokerage", "appraisal", "leasing", "property management",
    # Design
    "figma", "sketch", "photoshop", "illustrator", "ui design", "ux design",
    "wireframe", "prototype",
}

# Role levels for detecting seniority mismatch.
# Note: generic job titles like "engineer"/"developer" are intentionally excluded
# because they carry no seniority signal and would misclassify junior/senior CVs.
ROLE_LEVELS = {
    "intern": {"intern", "internship", "thực tập", "fresher", "trainee"},
    "junior": {"junior", "associate", "entry level", "entry-level", "1-2 years"},
    "mid": {"mid", "middle", "intermediate", "3-5 years"},
    "senior": {"senior", "lead", "principal", "staff", "architect", "7+ years", "5+ years"},
    "manager": {"manager", "director", "head", "chief", "vp", "vice president",
                "team lead", "tech lead", "quản lý", "trưởng phòng", "giám đốc"},
}

# Ordered from most junior to most senior; used for tie-breaking and distance.
ROLE_LEVEL_ORDER = ["intern", "junior", "mid", "senior", "manager"]

# Domain categories for detecting domain mismatch (universal - all industries)
DOMAIN_KEYWORDS = {
    # IT & Technology
    "cybersecurity": {"cybersecurity", "security", "siem", "threat", "vulnerability",
                      "penetration", "soc", "incident response", "malware", "forensic",
                      "firewall", "ids", "ips", "wireshark", "nmap", "burp suite",
                      "owasp", "encryption", "an ninh mạng", "bảo mật"},
    "web_development": {"react", "angular", "vue", "frontend", "backend", "fullstack",
                        "full-stack", "web development", "html", "css", "javascript",
                        "nodejs", "api", "rest", "graphql", "web developer"},
    "data_science": {"data science", "machine learning", "deep learning", "ai",
                     "artificial intelligence", "nlp", "computer vision", "tensorflow",
                     "pytorch", "data analysis", "statistics", "data scientist"},
    "devops": {"devops", "cloud", "aws", "azure", "gcp", "kubernetes", "docker",
               "terraform", "ci/cd", "infrastructure", "deployment", "sre",
               "cloud engineer", "site reliability"},
    "mobile": {"mobile", "ios", "android", "flutter", "react native", "swift",
               "kotlin", "mobile app", "ứng dụng di động", "mobile developer"},
    "enterprise_it": {"sap", "erp", "crm", "oracle", "plsql", "it manager",
                      "it director", "enterprise", "vendor", "stakeholder",
                      "business requirements", "help desk", "it projects",
                      "it infrastructure", "it operations"},
    "database": {"database", "dba", "sql", "oracle", "postgresql", "mysql",
                 "mongodb", "data modeling", "data warehouse", "etl", "data engineer"},
    # Business & Management
    "marketing": {"marketing", "digital marketing", "seo", "sem", "content marketing",
                  "social media", "brand", "campaign", "ads", "advertising",
                  "market research", "email marketing", "influencer", "pr",
                  "public relations", "google ads", "facebook ads", "analytics",
                  "tiếp thị", "quảng cáo", "truyền thông"},
    "sales": {"sales", "b2b", "b2c", "revenue", "pipeline", "crm", "negotiation",
              "account management", "business development", "lead generation",
              "quota", "territory", "closing", "prospecting", "client acquisition",
              "bán hàng", "kinh doanh", "doanh thu"},
    "human_resources": {"human resources", "hr", "recruitment", "hiring", "talent",
                        "onboarding", "employee relations", "compensation", "benefits",
                        "payroll", "performance management", "training", "development",
                        "labor law", "nhân sự", "tuyển dụng", "đào tạo"},
    "finance": {"finance", "accounting", "financial analysis", "budgeting", "forecasting",
                "audit", "tax", "investment", "banking", "portfolio", "risk management",
                "financial reporting", "compliance", "tài chính", "kế toán", "kiểm toán"},
    "operations": {"operations", "supply chain", "logistics", "procurement", "inventory",
                   "warehouse", "manufacturing", "production", "quality control",
                   "lean", "six sigma", "process improvement", "vận hành", "sản xuất"},
    "project_management": {"project management", "pmp", "scrum master", "agile",
                           "waterfall", "sprint", "backlog", "stakeholder management",
                           "risk management", "milestone", "deliverable", "gantt",
                           "quản lý dự án"},
    # Specialized Industries
    "healthcare": {"healthcare", "medical", "clinical", "patient", "hospital",
                   "nursing", "pharmacy", "diagnosis", "treatment", "physician",
                   "surgeon", "therapist", "health", "y tế", "bệnh viện", "bác sĩ"},
    "education": {"education", "teaching", "curriculum", "student", "classroom",
                  "pedagogy", "assessment", "learning", "instructor", "professor",
                  "academic", "school", "university", "giáo dục", "giảng dạy"},
    "legal": {"legal", "law", "attorney", "lawyer", "litigation", "contract",
              "compliance", "regulatory", "intellectual property", "corporate law",
              "dispute", "court", "luật", "pháp lý", "hợp đồng"},
    "design": {"design", "ui", "ux", "graphic design", "figma", "sketch", "adobe",
               "photoshop", "illustrator", "user experience", "user interface",
               "wireframe", "prototype", "thiết kế"},
    "construction": {"construction", "civil engineering", "structural", "autocad",
                     "building", "site supervision", "safety compliance", "contractor",
                     "architecture", "blueprint", "xây dựng", "kiến trúc"},
    "hospitality": {"hospitality", "hotel", "restaurant", "tourism", "travel",
                    "customer service", "front desk", "reservation", "event planning",
                    "food service", "khách sạn", "du lịch", "nhà hàng"},
    "real_estate": {"real estate", "property", "broker", "listing", "appraisal",
                    "mortgage", "lease", "tenant", "commercial property",
                    "bất động sản", "môi giới"},
}


def normalize_skill(skill: str) -> str:
    value = skill.lower().strip()
    return SKILL_SYNONYMS.get(value, value)


def _contains_skill(text: str, skill: str) -> bool:
    escaped = re.escape(skill)
    if skill in {"ci/cd", "rest api", "machine learning", "deep learning",
                 "c/c++", "log analysis", "threat detection", "incident response",
                 "vulnerability assessment", "penetration testing", "network security",
                 "project management", "github actions", "power bi", "random forest",
                 "neural network", "computer vision", "burp suite", "elk stack"}:
        return skill in text
    pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def extract_skills(text: str) -> set[str]:
    text_lower = text.lower()
    found: set[str] = set()
    for skill in KNOWN_SKILLS:
        if _contains_skill(text_lower, skill):
            found.add(normalize_skill(skill))
    for alias, canonical in SKILL_SYNONYMS.items():
        if _contains_skill(text_lower, alias):
            found.add(canonical)
    return found


# Indicators for must-have vs nice-to-have classification
MUST_HAVE_INDICATORS = {
    "required", "must have", "must-have", "essential", "mandatory",
    "minimum", "necessary", "critical", "key requirement",
    "bắt buộc", "yêu cầu", "tối thiểu", "cần có",
    "qualifications", "requirements", "responsibilities",
}

NICE_TO_HAVE_INDICATORS = {
    "preferred", "nice to have", "nice-to-have", "bonus", "plus",
    "advantage", "desirable", "optional", "good to have",
    "ưu tiên", "có thì tốt", "lợi thế", "mong muốn",
}


def _split_line_into_segments(line: str) -> list[tuple[str, str]]:
    """Tách một dòng thành các đoạn theo indicator must-have / nice-to-have.

    Trả về danh sách (segment_text, section) với section là 'must' hoặc 'nice'.
    Nhờ vậy dòng dạng "Required: Python. Nice to have: Docker" được tách thành
    đoạn must-have ("Python") và đoạn nice-to-have ("Docker") thay vì gộp chung.
    """
    # Tìm vị trí xuất hiện của mọi indicator trong dòng.
    markers: list[tuple[int, str]] = []
    for indicator in MUST_HAVE_INDICATORS:
        start = line.find(indicator)
        while start != -1:
            markers.append((start, "must"))
            start = line.find(indicator, start + 1)
    for indicator in NICE_TO_HAVE_INDICATORS:
        start = line.find(indicator)
        while start != -1:
            markers.append((start, "nice"))
            start = line.find(indicator, start + 1)

    markers.sort(key=lambda m: m[0])

    # Đoạn đầu (trước indicator đầu tiên) không mang section riêng -> None.
    segments: list[tuple[str, str | None]] = []
    if not markers:
        return [(line, None)]

    if markers[0][0] > 0:
        segments.append((line[: markers[0][0]], None))
    for idx, (pos, section) in enumerate(markers):
        end = markers[idx + 1][0] if idx + 1 < len(markers) else len(line)
        segments.append((line[pos:end], section))
    return segments


def classify_jd_skills(jd_text: str, jd_skills: set[str]) -> dict:
    """Classify JD skills into must-have and nice-to-have based on context.

    Xử lý được cả trường hợp must-have và nice-to-have nằm trên cùng một dòng
    bằng cách tách dòng thành các đoạn tại vị trí indicator.
    """
    text_lower = jd_text.lower()
    lines = text_lower.split('\n')

    must_have_skills: set[str] = set()
    nice_to_have_skills: set[str] = set()

    # Section mặc định khi chưa gặp indicator nào: must-have.
    current_section = "must"

    for line in lines:
        for segment, section in _split_line_into_segments(line):
            # Đoạn có indicator riêng thì cập nhật section hiện tại (giữ sang
            # các dòng/đoạn sau nếu không có indicator mới). Đoạn None kế thừa.
            if section is not None:
                current_section = section
            target = nice_to_have_skills if current_section == "nice" else must_have_skills
            for skill in jd_skills:
                if _contains_skill(segment, skill.lower()):
                    target.add(skill)

    # Một skill vừa xuất hiện ở vùng must-have vừa nice-to-have -> ưu tiên must-have.
    nice_to_have_skills -= must_have_skills

    # Skills không rơi vào đoạn nào (không khớp) mặc định là must-have.
    unclassified = jd_skills - must_have_skills - nice_to_have_skills
    must_have_skills.update(unclassified)

    return {
        "must_have": sorted(must_have_skills),
        "nice_to_have": sorted(nice_to_have_skills),
    }


def _contains_phrase(text: str, phrase: str) -> bool:
    """Word-boundary aware match so 'lead' doesn't match 'leader' or 'head' 'ahead'."""
    pattern = rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])"
    return re.search(pattern, text) is not None


# Tín hiệu lãnh đạo (không phải title) gợi ý cấp senior/manager.
LEADERSHIP_SIGNALS = {
    "led team", "led a team", "led the team", "managed team", "managed a team",
    "team lead", "leading team", "mentored", "mentoring", "coached",
    "quản lý nhóm", "dẫn dắt", "phụ trách nhóm",
}
MANAGEMENT_SIGNALS = {
    "stakeholder management", "stakeholder", "vendor management", "vendor",
    "budget", "roadmap", "hiring", "headcount", "p&l", "team size",
    "cross-functional", "quản lý ngân sách", "quản lý nhà cung cấp",
}


def detect_role_level(text: str, years: int | None = None) -> str:
    """Detect the seniority/role level from text.

    Ties are broken toward the more senior level (e.g. a JD mentioning both
    "junior" and "senior" is treated as senior), which is the safer default
    for screening.

    Nếu không có title rõ ràng, suy từ ngữ cảnh: số năm kinh nghiệm kết hợp
    tín hiệu lãnh đạo/quản lý (led team, stakeholder, vendor, budget...).
    """
    text_lower = text.lower()
    scores = {}
    for level, keywords in ROLE_LEVELS.items():
        count = sum(1 for kw in keywords if _contains_phrase(text_lower, kw))
        if count > 0:
            scores[level] = count

    if scores:
        best_count = max(scores.values())
        # Among levels tied on count, pick the most senior (highest order index).
        return max(
            (level for level, count in scores.items() if count == best_count),
            key=ROLE_LEVEL_ORDER.index,
        )

    # Không có title -> suy từ ngữ cảnh lãnh đạo + số năm.
    # Dùng word-boundary (như ROLE_LEVELS) để "team lead" không khớp "team leader".
    has_leadership = any(_contains_phrase(text_lower, sig) for sig in LEADERSHIP_SIGNALS)
    has_management = any(_contains_phrase(text_lower, sig) for sig in MANAGEMENT_SIGNALS)

    if years is not None:
        if years >= 7 and (has_management or has_leadership):
            return "manager"
        if years >= 5 and has_leadership:
            return "senior"
        # Explicit years are a strong seniority signal even when the CV/JD omits
        # words like junior/senior/lead. This reduces false "unknown" role matches.
        if years < 1:
            return "intern"
        if years <= 2:
            return "junior"
        if years <= 5:
            return "mid"
        return "senior"
    if has_management:
        return "manager"
    if has_leadership:
        return "senior"
    return "unknown"


# Map từng skill (đã normalize) sang các domain liên quan.
# Dùng để suy domain từ skill khi keyword domain trong text không đủ rõ.
SKILL_DOMAIN_MAP = {
    # Web / backend
    "python": ["web_development", "data_science"],
    "fastapi": ["web_development"],
    "django": ["web_development"],
    "flask": ["web_development"],
    "nodejs": ["web_development"],
    "express": ["web_development"],
    "spring": ["web_development"],
    "dotnet": ["web_development"],
    "laravel": ["web_development"],
    "rails": ["web_development"],
    "react": ["web_development"],
    "angular": ["web_development"],
    "vuejs": ["web_development"],
    "nextjs": ["web_development"],
    "rest api": ["web_development"],
    "graphql": ["web_development"],
    # Database
    "postgresql": ["database", "web_development"],
    "mysql": ["database"],
    "mongodb": ["database"],
    "oracle": ["database", "enterprise_it"],
    "plsql": ["database", "enterprise_it"],
    "mssql": ["database"],
    # DevOps
    "docker": ["devops"],
    "kubernetes": ["devops"],
    "terraform": ["devops"],
    "ansible": ["devops"],
    "jenkins": ["devops"],
    "aws": ["devops"],
    "gcp": ["devops"],
    "azure": ["devops"],
    # Data science
    "machine learning": ["data_science"],
    "deep learning": ["data_science"],
    "tensorflow": ["data_science"],
    "pytorch": ["data_science"],
    "nlp": ["data_science"],
    "pandas": ["data_science"],
    # Security
    "siem": ["cybersecurity"],
    "wireshark": ["cybersecurity"],
    "nmap": ["cybersecurity"],
    "wazuh": ["cybersecurity"],
    "penetration testing": ["cybersecurity"],
    "burp suite": ["cybersecurity"],
    # Mobile
    "swift": ["mobile"],
    "kotlin": ["mobile"],
    # Marketing
    "seo": ["marketing"],
    "sem": ["marketing"],
    "google ads": ["marketing"],
    "facebook ads": ["marketing"],
    "content marketing": ["marketing"],
    "social media": ["marketing"],
    "branding": ["marketing"],
    "email marketing": ["marketing"],
    "google analytics": ["marketing"],
    # Sales
    "lead generation": ["sales"],
    "account management": ["sales"],
    "business development": ["sales"],
    "pipeline management": ["sales"],
    "b2b sales": ["sales"],
    "b2c sales": ["sales"],
    # HR
    "recruitment": ["human_resources"],
    "onboarding": ["human_resources"],
    "payroll": ["human_resources"],
    "talent acquisition": ["human_resources"],
    "compensation": ["human_resources"],
    # Finance
    "financial analysis": ["finance"],
    "accounting": ["finance"],
    "audit": ["finance"],
    "tax": ["finance"],
    "budgeting": ["finance"],
    "financial reporting": ["finance"],
    # Design
    "figma": ["design"],
    "ui design": ["design"],
    "ux design": ["design"],
    "photoshop": ["design"],
    # Enterprise IT
    "sap": ["enterprise_it"],
    "erp": ["enterprise_it"],
}


def infer_domains_from_skills(skills: set[str]) -> list[str]:
    """Suy domain từ tập skill đã trích xuất (đã normalize)."""
    domains: set[str] = set()
    for skill in skills:
        for domain in SKILL_DOMAIN_MAP.get(skill, []):
            domains.add(domain)
    return sorted(domains)


def detect_domains(text: str, skills: set[str] | None = None) -> list[str]:
    """Detect which domains/fields are mentioned in text.

    Uses word-boundary matching so short tokens like 'api' or 'rest' don't
    match inside unrelated words, and requires at least two distinct keyword
    hits so a single incidental mention doesn't tag a whole domain.

    Nếu keyword không đủ để xác định domain, suy thêm từ skill (skill->domain).
    """
    text_lower = text.lower()
    domains = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        count = sum(1 for kw in keywords if _contains_phrase(text_lower, kw))
        if count >= 2:
            domains.append(domain)

    # Bổ sung domain suy từ skill (giúp JD/CV chỉ liệt kê skill vẫn ra domain).
    if skills:
        for domain in infer_domains_from_skills(skills):
            if domain not in domains:
                domains.append(domain)
    return domains


def calculate_role_compatibility(cv_level: str, jd_level: str) -> float:
    """Calculate compatibility between CV role level and JD role level."""
    if cv_level == "unknown" or jd_level == "unknown":
        return 60.0

    if cv_level not in ROLE_LEVEL_ORDER or jd_level not in ROLE_LEVEL_ORDER:
        return 60.0

    cv_idx = ROLE_LEVEL_ORDER.index(cv_level)
    jd_idx = ROLE_LEVEL_ORDER.index(jd_level)
    diff = abs(cv_idx - jd_idx)

    if diff == 0:
        return 100.0
    elif diff == 1:
        return 70.0
    elif diff == 2:
        return 40.0
    elif diff == 3:
        return 20.0
    else:
        return 5.0


def calculate_domain_compatibility(cv_domains: list[str], jd_domains: list[str]) -> float:
    """Calculate compatibility between CV domains and JD domains."""
    if not cv_domains or not jd_domains:
        return 50.0

    cv_set = set(cv_domains)
    jd_set = set(jd_domains)

    overlap = cv_set & jd_set
    if overlap:
        return round(len(overlap) / len(jd_set) * 100, 2)
    return 10.0


def extract_years_experience(text: str) -> int | None:
    """Trích số năm kinh nghiệm từ CV/JD.

    Ưu tiên các cụm rõ ràng ("5 years of experience", "tối thiểu 3 năm",
    "3+ years"...). Nếu không có, mới suy từ khoảng thời gian dạng năm
    ("2019 - 2024") như phương án cuối, lấy khoảng dài nhất.
    """
    text_lower = text.lower()
    patterns = [
        # "5 years of experience", "5+ yrs experience"
        r"(\d{1,2})\+?\s*(?:years|year|yrs|yr)\s+(?:of\s+)?experience",
        # "minimum/at least/over/more than 3 years"
        r"(?:minimum|at least|over|more than|min\.?)\s+(?:of\s+)?(\d{1,2})\+?\s*(?:years|year|yrs|yr)",
        # "experience: ... 3 years" / "experience of 3 years" (giới hạn khoảng cách)
        r"(?:experience|kinh nghiệm)[^\d]{0,30}(\d{1,2})\+?\s*(?:years|year|năm)",
        # "3+ years" / "3+ năm" đứng riêng (bắt buộc có dấu +)
        r"(\d{1,2})\+\s*(?:years|year|yrs|yr|năm)",
        # Tiếng Việt: "3 năm kinh nghiệm"
        r"(\d{1,2})\+?\s*năm\s+kinh\s+nghiệm",
        # Tiếng Việt: "tối thiểu/trên/từ/ít nhất 3 năm"
        r"(?:tối thiểu|trên|từ|ít nhất)\s+(\d{1,2})\+?\s*năm",
    ]
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return int(match.group(1))

    # Phương án cuối: khoảng năm "2019 - 2024" -> lấy khoảng dài nhất (<= 40 năm).
    # Also supports open-ended ranges like "2021 - present/current/now".
    current_year = datetime.utcnow().year
    ranges = re.findall(
        r"\b(19\d{2}|20\d{2})\s*[-–—]\s*(19\d{2}|20\d{2}|present|current|now|nay|hiện\s+tại)\b",
        text_lower,
    )
    spans = []
    for start, end in ranges:
        end_year = current_year if not end[:4].isdigit() else int(end[:4])
        span = end_year - int(start)
        if 0 <= span <= 40:
            spans.append(span)
    if spans:
        return max(spans)
    return None


def get_compatibility_level(score: float) -> dict:
    if score >= 85:
        return {
            "level": "Rất phù hợp",
            "recommendation": "Rất nên tuyển",
            "message": "Ứng viên rất phù hợp với JD.",
        }
    if score >= 70:
        return {
            "level": "Phù hợp tốt",
            "recommendation": "Nên tuyển",
            "message": "Ứng viên phù hợp, có thể đưa vào vòng phỏng vấn.",
        }
    if score >= 55:
        return {
            "level": "Phù hợp trung bình",
            "recommendation": "Cân nhắc thêm",
            "message": "Ứng viên có mức phù hợp trung bình, cần kiểm tra thêm.",
        }
    if score >= 40:
        return {
            "level": "Phù hợp thấp",
            "recommendation": "Không ưu tiên",
            "message": "Ứng viên còn thiếu nhiều yêu cầu quan trọng.",
        }
    return {
        "level": "Không phù hợp",
        "recommendation": "Từ chối",
        "message": "CV chưa phù hợp với JD hiện tại.",
    }


# \w với re.UNICODE bắt cả chữ có dấu tiếng Việt; giữ độ dài >= 3 để bỏ từ quá ngắn.
_WORD_RE = re.compile(r"[^\W\d_]{3,}", re.UNICODE)

# Stopword Anh + Việt (từ chức năng, không mang thông tin phân biệt).
_KEYWORD_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "have",
    "are", "was", "will", "can", "not", "you", "your", "our",
    "his", "her", "its", "they", "them", "their", "all", "any",
    "each", "every", "both", "few", "more", "most", "other",
    "và", "các", "của", "cho", "với", "được", "trong", "khi", "này",
    "đó", "là", "có", "những", "một", "để", "theo", "hoặc", "như",
}


def calculate_keyword_score(cv_text: str, jd_text: str) -> float:
    jd_words = set(_WORD_RE.findall(jd_text.lower()))
    if not jd_words:
        return 0.0
    cv_words = set(_WORD_RE.findall(cv_text.lower()))
    jd_keywords = jd_words - _KEYWORD_STOPWORDS
    if not jd_keywords:
        return 0.0
    matched = cv_words & jd_keywords
    return round(len(matched) / len(jd_keywords) * 100, 2)


def calculate_cv_quality(cv_text: str) -> float:
    score = 50.0
    if len(cv_text) > 300:
        score += 10
    if len(cv_text) > 800:
        score += 5
    if re.search(r"\d+%|\d+\s*(users|requests|projects|clients)", cv_text.lower()):
        score += 15
    section_keywords = ["experience", "education", "skills", "projects",
                        "kinh nghiệm", "học vấn", "kỹ năng", "certificate",
                        "chứng chỉ", "dự án"]
    sections_found = sum(1 for kw in section_keywords if kw in cv_text.lower())
    score += min(sections_found * 5, 20)
    return min(score, 100.0)


def calculate_matching(cv_text: str, jd_text: str) -> dict:
    cv_skills = extract_skills(cv_text)
    jd_skills = extract_skills(jd_text)

    matched_skills = sorted(cv_skills & jd_skills)
    missing_skills = sorted(jd_skills - cv_skills)
    extra_skills = sorted(cv_skills - jd_skills)

    # Classify JD skills into must-have and nice-to-have
    skill_classification = classify_jd_skills(jd_text, jd_skills)
    must_have_skills = set(skill_classification["must_have"])
    nice_to_have_skills = set(skill_classification["nice_to_have"])

    # Calculate weighted skill score: must-have 70%, nice-to-have 30%
    matched_must_have = sorted(cv_skills & must_have_skills)
    matched_nice_to_have = sorted(cv_skills & nice_to_have_skills)
    missing_must_have = sorted(must_have_skills - cv_skills)
    missing_nice_to_have = sorted(nice_to_have_skills - cv_skills)

    must_have_score = round(len(matched_must_have) / len(must_have_skills) * 100, 2) if must_have_skills else 0.0
    nice_to_have_score = round(len(matched_nice_to_have) / len(nice_to_have_skills) * 100, 2) if nice_to_have_skills else 0.0

    # Weighted skill score
    if must_have_skills and nice_to_have_skills:
        skill_score = round(must_have_score * 0.70 + nice_to_have_score * 0.30, 2)
    elif must_have_skills:
        skill_score = must_have_score
    elif nice_to_have_skills:
        skill_score = nice_to_have_score
    else:
        skill_score = 0.0

    candidate_years = extract_years_experience(cv_text)
    required_years = extract_years_experience(jd_text)
    if candidate_years is not None and required_years:
        experience_score = round(min(candidate_years / required_years, 1) * 100, 2)
    else:
        experience_score = 50.0  # unknown = neutral, not "medium fit"

    education_keywords = ["bachelor", "degree", "university", "computer science",
                          "đại học", "cử nhân", "master", "phd", "thạc sĩ", "tiến sĩ"]
    education_score = 100.0 if any(keyword in cv_text.lower() for keyword in education_keywords) else 50.0

    keyword_score = calculate_keyword_score(cv_text, jd_text)
    cv_quality_score = calculate_cv_quality(cv_text)

    # Role level analysis. Truyền số năm để suy cấp bậc từ ngữ cảnh (led team,
    # stakeholder, budget...) khi CV/JD không có title rõ ràng.
    cv_role_level = detect_role_level(cv_text, candidate_years)
    jd_role_level = detect_role_level(jd_text, required_years)
    role_compatibility = calculate_role_compatibility(cv_role_level, jd_role_level)

    # Domain analysis
    cv_domains = detect_domains(cv_text, cv_skills)
    jd_domains = detect_domains(jd_text, jd_skills)
    domain_compatibility = calculate_domain_compatibility(cv_domains, jd_domains)

    # Weighted overall score (optimized weights)
    # Skill + Role + Domain = 70% (most decisive factors)
    # Experience + Education + Keyword + CV Quality = 30% (supporting factors)
    overall_score = round(
        skill_score * 0.35
        + role_compatibility * 0.20
        + domain_compatibility * 0.15
        + experience_score * 0.15
        + education_score * 0.05
        + keyword_score * 0.05
        + cv_quality_score * 0.05,
        2,
    )

    # Score cap rules: prevent inflated scores when critical mismatches exist
    if role_compatibility <= 20 and domain_compatibility <= 20:
        overall_score = min(overall_score, 35.0)
    elif role_compatibility <= 20 or domain_compatibility <= 20:
        overall_score = min(overall_score, 45.0)
    if skill_score <= 20 and domain_compatibility <= 30:
        overall_score = min(overall_score, 40.0)
    # Cap if all must-have skills are missing
    if must_have_skills and must_have_score == 0:
        overall_score = min(overall_score, 40.0)

    compatibility = get_compatibility_level(overall_score)

    return {
        "matching_score": overall_score,
        "skill_score": skill_score,
        "must_have_score": must_have_score,
        "nice_to_have_score": nice_to_have_score,
        "experience_score": experience_score,
        "education_score": education_score,
        "keyword_score": keyword_score,
        "cv_quality_score": cv_quality_score,
        "role_compatibility": role_compatibility,
        "domain_compatibility": domain_compatibility,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "extra_skills": extra_skills,
        "matched_must_have": matched_must_have,
        "missing_must_have": missing_must_have,
        "matched_nice_to_have": matched_nice_to_have,
        "missing_nice_to_have": missing_nice_to_have,
        "candidate_years": candidate_years,
        "required_years": required_years,
        "cv_role_level": cv_role_level,
        "jd_role_level": jd_role_level,
        "cv_domains": cv_domains,
        "jd_domains": jd_domains,
        "compatibility": compatibility,
        "score_breakdown": {
            "skill_match": {
                "score": skill_score,
                "weight": 35,
                "description": f"Kỹ năng bắt buộc: {must_have_score:.0f}% | Kỹ năng ưu tiên: {nice_to_have_score:.0f}%",
            },
            "role_match": {
                "score": role_compatibility,
                "weight": 20,
                "description": f"Mức độ phù hợp cấp bậc ({cv_role_level} vs {jd_role_level})",
            },
            "domain_match": {
                "score": domain_compatibility,
                "weight": 15,
                "description": "Mức độ phù hợp lĩnh vực chuyên môn",
            },
            "experience_match": {
                "score": experience_score,
                "weight": 15,
                "description": "Mức độ phù hợp về kinh nghiệm làm việc",
            },
            "education_match": {
                "score": education_score,
                "weight": 5,
                "description": "Mức độ phù hợp về học vấn",
            },
            "keyword_match": {
                "score": keyword_score,
                "weight": 5,
                "description": "Mức độ khớp các từ khóa quan trọng trong JD",
            },
            "cv_quality": {
                "score": cv_quality_score,
                "weight": 5,
                "description": "Chất lượng trình bày và mức độ rõ ràng của CV",
            },
        },
    }
