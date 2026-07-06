import json
import requests

from app.ai.base import AIService
from app.core.config import settings


class OllamaAIService(AIService):
    def generate_feedback(self, matching_result: dict) -> dict:
        prompt = f"""
You are an interview preparation assistant.
Return valid JSON only. Do not return markdown.
Use only this structured input:
{json.dumps(matching_result, ensure_ascii=False)}

Output schema:
{{
  "summary": "string",
  "strengths": ["string"],
  "weaknesses": ["string"],
  "improvement_suggestions": ["string"],
  "interview_questions": ["string"]
}}
"""
        response = requests.post(
            f"{settings.ollama_base_url}/api/generate",
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False, "format": "json"},
            timeout=settings.ai_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        raw = data.get("response", "{}")
        ai_result = json.loads(raw)
        return self.ensure_full_contract(matching_result, ai_result)
