"""Слой ИИ.

Здесь же живёт зависимость для FastAPI. Клиент один на процесс: поднимать
пул соединений на каждый запрос незачем.

Если ключ DeepSeek не задан, подставляется заглушка. Это осознанное
поведение, а не аварийный режим: приложение можно собрать, пройти и
показать без единого обращения к платному API, а потом положить ключ
в .env — код при этом не меняется.
"""

import logging
from functools import lru_cache

from app.ai.client import DeepSeekClient, LLMClient
from app.ai.stub import StubLLMClient
from app.config import get_settings

logger = logging.getLogger(__name__)

__all__ = ["DeepSeekClient", "LLMClient", "StubLLMClient", "get_llm_client"]


@lru_cache
def _client() -> LLMClient:
    settings = get_settings()
    if not settings.use_real_llm:
        logger.warning(
            "DEEPSEEK_API_KEY пуст — работаем на заглушке. "
            "Маршруты будут шаблонными."
        )
        return StubLLMClient()
    return DeepSeekClient(
        settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        timeout=settings.deepseek_timeout_seconds,
    )


def get_llm_client() -> LLMClient:
    """Зависимость FastAPI. В тестах подменяется через dependency_overrides."""
    return _client()
