from app.ai.base import AIService


# Alternative role suggestions based on domain
ALTERNATIVE_ROLES_BY_DOMAIN = {
    "cybersecurity": [
        "Cybersecurity Engineer", "SOC Analyst", "SIEM Analyst",
        "Security Monitoring Engineer", "Penetration Tester",
        "Incident Response Analyst", "Security Operations Analyst",
    ],
    "web_development": [
        "Frontend Developer", "Backend Developer", "Full-Stack Developer",
        "Web Developer", "Software Engineer", "UI Developer",
    ],
    "data_science": [
        "Data Scientist", "Machine Learning Engineer", "Data Analyst",
        "AI Engineer", "Research Scientist", "NLP Engineer",
    ],
    "devops": [
        "DevOps Engineer", "Cloud Engineer", "SRE Engineer",
        "Infrastructure Engineer", "Platform Engineer", "Systems Administrator",
    ],
    "mobile": [
        "Mobile Developer", "iOS Developer", "Android Developer",
        "Flutter Developer", "React Native Developer",
    ],
    "enterprise_it": [
        "IT Manager", "IT Project Manager", "Systems Administrator",
        "IT Operations Manager", "ERP Consultant", "SAP Consultant",
    ],
    "database": [
        "Database Administrator", "Data Engineer", "ETL Developer",
        "Database Developer", "Data Architect",
    ],
    "marketing": [
        "Digital Marketing Specialist", "Content Marketing Manager",
        "SEO Specialist", "Social Media Manager", "Marketing Analyst",
        "Brand Manager", "Growth Hacker",
    ],
    "sales": [
        "Sales Executive", "Account Manager", "Business Development Manager",
        "Sales Representative", "Key Account Manager", "Sales Engineer",
    ],
    "human_resources": [
        "HR Manager", "Recruiter", "Talent Acquisition Specialist",
        "HR Business Partner", "Compensation & Benefits Specialist",
    ],
    "finance": [
        "Financial Analyst", "Accountant", "Auditor",
        "Investment Analyst", "Risk Analyst", "Finance Manager",
    ],
    "operations": [
        "Operations Manager", "Supply Chain Manager", "Logistics Coordinator",
        "Production Manager", "Quality Assurance Manager",
    ],
    "project_management": [
        "Project Manager", "Scrum Master", "Product Owner",
        "Program Manager", "Delivery Manager",
    ],
    "healthcare": [
        "Healthcare Administrator", "Clinical Coordinator",
        "Medical Officer", "Health Informatics Specialist",
    ],
    "education": [
        "Teacher", "Instructor", "Curriculum Developer",
        "Training Specialist", "Academic Coordinator",
    ],
    "legal": [
        "Legal Counsel", "Compliance Officer", "Contract Manager",
        "Paralegal", "Legal Analyst",
    ],
    "design": [
        "UI/UX Designer", "Graphic Designer", "Product Designer",
        "Visual Designer", "Interaction Designer",
    ],
    "construction": [
        "Site Engineer", "Project Engineer", "Construction Manager",
        "Civil Engineer", "Structural Engineer",
    ],
    "hospitality": [
        "Hotel Manager", "Front Office Manager", "Event Coordinator",
        "Restaurant Manager", "Tourism Specialist",
    ],
    "real_estate": [
        "Real Estate Agent", "Property Manager", "Real Estate Analyst",
        "Leasing Manager", "Real Estate Consultant",
    ],
}


class MockAIService(AIService):
    def generate_feedback(self, matching_result: dict) -> dict:
        missing = matching_result.get("missing_skills", [])
        matched = matching_result.get("matched_skills", [])
        score = matching_result.get("matching_score", 0)
        compatibility = matching_result.get("compatibility", {})
        cv_domains = matching_result.get("cv_domains", [])
        jd_domains = matching_result.get("jd_domains", [])
        cv_role_level = matching_result.get("cv_role_level", "unknown")
        jd_role_level = matching_result.get("jd_role_level", "unknown")

        summary = self._create_summary(score)
        strengths = self._create_strengths(matched)
        weaknesses = self._create_weaknesses(missing)
        risk_flags = self._create_risk_flags(missing, cv_role_level, jd_role_level, cv_domains, jd_domains)
        recruiter_recs = self._create_recruiter_recommendations(score, missing, cv_domains, jd_domains)
        candidate_recs = self._create_candidate_recommendations(missing, cv_domains, jd_domains)
        questions = self._create_interview_questions(missing, matched)
        alternative_roles = self._suggest_alternative_roles(cv_domains, cv_role_level)

        return {
            "summary": summary,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "risk_flags": risk_flags,
            "recommendations": {
                "for_recruiter": recruiter_recs,
                "for_candidate": candidate_recs,
            },
            "improvement_suggestions": candidate_recs,
            "interview_questions": questions,
            "alternative_roles": alternative_roles,
        }

    def _create_summary(self, score: float) -> str:
        if score >= 85:
            return "CV có độ phù hợp rất cao với JD. Ứng viên đáp ứng tốt hầu hết yêu cầu tuyển dụng."
        if score >= 70:
            return "CV có độ phù hợp tốt với JD. Ứng viên có nhiều kỹ năng liên quan và nên được đưa vào vòng phỏng vấn."
        if score >= 55:
            return "CV có độ phù hợp trung bình. Ứng viên có nền tảng phù hợp nhưng cần bổ sung thêm một số kỹ năng hoặc bằng chứng dự án."
        if score >= 40:
            return "CV có độ phù hợp thấp. Ứng viên còn thiếu nhiều yêu cầu quan trọng so với JD."
        return "CV chưa phù hợp với JD hiện tại."

    def _create_strengths(self, matched_skills: list[str]) -> list[str]:
        if not matched_skills:
            return ["CV chưa thể hiện rõ các kỹ năng trùng với JD."]
        return [
            f"Có các kỹ năng phù hợp với JD: {', '.join(matched_skills)}.",
            "Có thể dùng kết quả matching để định hướng vòng phỏng vấn kỹ thuật.",
        ]

    def _create_weaknesses(self, missing_skills: list[str]) -> list[str]:
        if not missing_skills:
            return ["Chưa phát hiện thiếu hụt kỹ năng lớn so với JD."]
        return [
            f"Thiếu các kỹ năng quan trọng trong JD: {', '.join(missing_skills)}.",
            "CV nên bổ sung thêm ví dụ dự án thực tế để tăng độ tin cậy.",
        ]

    def _create_risk_flags(self, missing_skills: list[str], cv_level: str,
                           jd_level: str, cv_domains: list, jd_domains: list) -> list[str]:
        risks = []

        # Role level mismatch
        level_order = ["intern", "junior", "mid", "senior", "manager"]
        if cv_level in level_order and jd_level in level_order:
            diff = abs(level_order.index(cv_level) - level_order.index(jd_level))
            if diff >= 3:
                risks.append(f"Lệch cấp bậc nghiêm trọng: CV là {cv_level}, JD yêu cầu {jd_level}.")
            elif diff >= 2:
                risks.append(f"Lệch cấp bậc đáng kể: CV là {cv_level}, JD yêu cầu {jd_level}.")

        # Domain mismatch
        if cv_domains and jd_domains and not set(cv_domains) & set(jd_domains):
            risks.append(f"Lĩnh vực không trùng khớp: CV thuộc {', '.join(cv_domains)}, JD thuộc {', '.join(jd_domains)}.")

        # Critical missing skills
        important_skills = {"aws", "docker", "kubernetes", "sap", "oracle", "java",
                           "python", "react", "angular", "plsql", "sdlc"}
        for skill in missing_skills:
            if skill.lower() in important_skills:
                risks.append(f"Thiếu kỹ năng quan trọng: {skill}.")

        if not risks:
            risks.append("Không phát hiện rủi ro lớn.")
        return risks

    def _create_recruiter_recommendations(self, score: float, missing_skills: list[str],
                                          cv_domains: list, jd_domains: list) -> list[str]:
        recs = []
        if score >= 70:
            recs.append("Nên đưa ứng viên vào vòng phỏng vấn tiếp theo.")
        elif score >= 55:
            recs.append("Có thể cân nhắc phỏng vấn nếu nguồn ứng viên chưa nhiều.")
        elif score >= 40:
            recs.append("Không nên ưu tiên ứng viên này cho vị trí hiện tại.")
        else:
            recs.append("Không khuyến nghị ứng viên này cho vị trí hiện tại.")
            if cv_domains:
                domain_names = ", ".join(cv_domains)
                recs.append(f"Ứng viên phù hợp hơn với các vị trí trong lĩnh vực: {domain_names}.")

        if missing_skills:
            recs.append(f"Nên hỏi kỹ về các kỹ năng còn thiếu: {', '.join(missing_skills[:5])}.")
        recs.append("Nên yêu cầu ứng viên mô tả dự án thực tế đã từng tham gia.")
        return recs

    def _create_candidate_recommendations(self, missing_skills: list[str],
                                          cv_domains: list, jd_domains: list) -> list[str]:
        suggestions = [
            "Đưa các kỹ năng khớp với JD lên phần đầu CV.",
            "Bổ sung mô tả dự án thực tế, vai trò cụ thể và kết quả đạt được.",
            "Viết rõ công nghệ đã dùng, quy mô hệ thống và trách nhiệm cá nhân.",
        ]
        if missing_skills:
            suggestions.append(f"Bổ sung hoặc làm rõ kinh nghiệm liên quan đến: {', '.join(missing_skills[:5])}.")

        # Domain mismatch advice
        if cv_domains and jd_domains and not set(cv_domains) & set(jd_domains):
            suggestions.append(
                f"CV thuộc lĩnh vực {', '.join(cv_domains)} nhưng JD yêu cầu {', '.join(jd_domains)}. "
                "Nên apply các vị trí phù hợp hơn với năng lực hiện tại."
            )
        return suggestions

    def _create_interview_questions(self, missing_skills: list[str], matched_skills: list[str]) -> list[str]:
        questions = []
        for skill in matched_skills[:3]:
            questions.append(f"Bạn hãy mô tả kinh nghiệm thực tế của bạn với {skill}?")
        for skill in missing_skills[:3]:
            questions.append(f"Bạn đã từng làm việc với {skill} chưa? Nếu có, hãy mô tả dự án cụ thể.")
        questions.append("Bạn hãy mô tả một dự án gần nhất và vai trò cụ thể của bạn trong dự án đó.")
        questions.append("Bạn đã từng gặp một khó khăn lớn trong công việc và đã xử lý nó như thế nào?")
        return questions

    def _suggest_alternative_roles(self, cv_domains: list[str], cv_level: str) -> list[str]:
        """Suggest alternative roles based on CV domain and level."""
        if not cv_domains:
            return []

        roles = []
        for domain in cv_domains:
            domain_roles = ALTERNATIVE_ROLES_BY_DOMAIN.get(domain, [])
            for role in domain_roles[:4]:
                # Add level suffix if applicable
                if cv_level == "intern":
                    roles.append(f"{role} Intern")
                elif cv_level == "junior":
                    roles.append(f"Junior {role}")
                else:
                    roles.append(role)

        return roles[:6]  # Return max 6 suggestions
