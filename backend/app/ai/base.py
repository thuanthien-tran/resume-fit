from abc import ABC, abstractmethod


class AIService(ABC):
    @abstractmethod
    def generate_feedback(self, matching_result: dict) -> dict:
        pass

    @staticmethod
    def ensure_full_contract(matching_result: dict, ai_result: dict) -> dict:
        """Guarantee the full result contract regardless of provider.

        The LLM providers (Ollama/xAI) typically only return narrative fields
        (summary, strengths, weaknesses, improvement_suggestions,
        interview_questions). The recruiter recommendations, risk flags and
        alternative roles are deterministic rule-based derivations, so we fill
        any missing/empty keys from the deterministic Mock generator. This keeps
        the "Recommendations" tab, risk flags and alternative roles populated
        even when a real AI provider is configured.
        """
        # Lazy import to avoid a circular import (mock_ai imports this module).
        from app.ai.mock_ai import MockAIService

        fallback = MockAIService().generate_feedback(matching_result)
        merged = dict(ai_result or {})

        # Deterministic fields: use the LLM value only if it is non-empty.
        for key in ("risk_flags", "recommendations", "alternative_roles", "improvement_suggestions"):
            if not merged.get(key):
                merged[key] = fallback[key]

        # Narrative fields: keep the LLM value, fall back only if absent.
        for key in ("summary", "strengths", "weaknesses", "interview_questions"):
            if merged.get(key) in (None, "", [], {}):
                merged[key] = fallback[key]

        return merged
