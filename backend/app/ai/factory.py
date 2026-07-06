from app.ai.base import AIService
from app.ai.mock_ai import MockAIService
from app.ai.ollama_ai import OllamaAIService
from app.ai.openai_ai import OpenAIService
from app.ai.xai_ai import XAIService
from app.core.config import settings


def get_ai_service() -> AIService:
    if settings.ai_provider == "ollama":
        return OllamaAIService()
    if settings.ai_provider == "xai":
        return XAIService()
    if settings.ai_provider == "openai":
        return OpenAIService()
    return MockAIService()