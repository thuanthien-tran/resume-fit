import json
import logging

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


CV_EXTRACTION_PROMPT = """You are a resume/CV parsing assistant. Extract structured information from this CV text.
Return ONLY valid JSON, no markdown, no explanation.

CV Text:
{cv_text}

Output JSON schema (fill all fields, use null if not found):
{{
  "candidate_role": "string - the role/position the candidate is targeting",
  "candidate_level": "string - one of: intern, junior, mid, senior, manager, unknown",
  "candidate_domain": "string - primary domain like: cybersecurity, web_development, data_science, devops, mobile, enterprise_it, marketing, sales, human_resources, finance, operations, healthcare, education, legal, design, construction, other",
  "years_of_experience": null or number,
  "education": {{
    "degree": "string or null",
    "major": "string or null",
    "institution": "string or null"
  }},
  "hard_skills": ["list of technical/hard skills found"],
  "soft_skills": ["list of soft skills found"],
  "tools": ["list of tools/software mentioned"],
  "projects": ["list of project names or descriptions"],
  "certifications": ["list of certifications"],
  "languages": ["list of spoken languages"],
  "evidence_strength": "string - one of: strong, medium, weak"
}}"""


JD_EXTRACTION_PROMPT = """You are a job description parsing assistant. Extract structured information from this JD text.
Return ONLY valid JSON, no markdown, no explanation.

JD Text:
{jd_text}

Output JSON schema (fill all fields, use null if not found):
{{
  "target_role": "string - the job title/role being recruited",
  "target_level": "string - one of: intern, junior, mid, senior, manager, director, unknown",
  "target_domain": "string - primary domain like: cybersecurity, web_development, data_science, devops, mobile, enterprise_it, marketing, sales, human_resources, finance, operations, healthcare, education, legal, design, construction, other",
  "required_experience_years": null or number,
  "must_have_skills": ["list of required/mandatory skills"],
  "nice_to_have_skills": ["list of preferred/optional skills"],
  "must_have_responsibilities": ["list of key responsibilities"],
  "education_requirements": ["list of education requirements"],
  "benefits": ["list of benefits mentioned"],
  "company_info": "string or null - brief company description if mentioned"
}}"""


def extract_cv_profile(cv_text: str) -> dict | None:
    """Extract structured profile from CV text using Ollama LLM."""
    if settings.ai_provider == "mock":
        return None

    try:
        prompt = CV_EXTRACTION_PROMPT.format(cv_text=cv_text[:3000])
        response = requests.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=settings.ai_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        raw = data.get("response", "{}")
        return json.loads(raw)
    except Exception as e:
        logger.warning("Failed to extract CV profile via Ollama: %s", e)
        return None


def extract_jd_profile(jd_text: str) -> dict | None:
    """Extract structured profile from JD text using Ollama LLM."""
    if settings.ai_provider == "mock":
        return None

    try:
        prompt = JD_EXTRACTION_PROMPT.format(jd_text=jd_text[:3000])
        response = requests.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=settings.ai_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        raw = data.get("response", "{}")
        return json.loads(raw)
    except Exception as e:
        logger.warning("Failed to extract JD profile via Ollama: %s", e)
        return None


def extract_profiles(cv_text: str, jd_text: str) -> dict:
    """Extract both CV and JD profiles. Returns dict with cv_profile and jd_profile."""
    cv_profile = extract_cv_profile(cv_text)
    jd_profile = extract_jd_profile(jd_text)

    return {
        "cv_profile": cv_profile,
        "jd_profile": jd_profile,
        "extraction_available": cv_profile is not None and jd_profile is not None,
    }
