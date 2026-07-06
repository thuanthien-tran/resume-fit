import json
import requests

from app.ai.base import AIService
from app.core.config import settings


class XAIService(AIService):
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
            f"{settings.xai_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.xai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.xai_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
            timeout=settings.ai_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        raw = data["choices"][0]["message"]["content"]
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        ai_result = json.loads(raw)
        return self.ensure_full_contract(matching_result, ai_result)
