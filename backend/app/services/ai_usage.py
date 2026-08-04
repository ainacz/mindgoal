"""Запись расхода токенов.

Слой ИИ в базу не ходит — он только возвращает usage. Записывает сюда
сервис. Это же место отвечает на вопрос «работает ли кэш»: если
cached_tokens стабильно ноль, значит системный промпт где-то собирается
из переменных и префикс не совпадает между запросами.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import AiCallKind
from app.models import AiCall
from app.schemas.ai import TokenUsage

# Цены DeepSeek за миллион токенов, август 2026. Нужны только для оценки
# в логах и админке — счёт всё равно приходит от провайдера.
PRICE_INPUT_MISS = 0.14
PRICE_INPUT_HIT = 0.0028
PRICE_OUTPUT = 0.28


def estimate_cost_usd(usage: TokenUsage) -> float:
    hit = usage.prompt_cache_hit_tokens
    miss = usage.prompt_cache_miss_tokens or max(usage.prompt_tokens - hit, 0)
    return (
        hit * PRICE_INPUT_HIT
        + miss * PRICE_INPUT_MISS
        + usage.completion_tokens * PRICE_OUTPUT
    ) / 1_000_000


async def record_ai_call(
    session: AsyncSession,
    *,
    user_id: int,
    kind: AiCallKind,
    model: str,
    usage: TokenUsage,
    latency_ms: int,
    goal_id: uuid.UUID | None = None,
    ok: bool = True,
    error: str | None = None,
) -> AiCall:
    call = AiCall(
        user_id=user_id,
        goal_id=goal_id,
        kind=kind,
        model=model,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        cached_tokens=usage.prompt_cache_hit_tokens,
        latency_ms=latency_ms,
        ok=ok,
        error=error[:2000] if error else None,
    )
    session.add(call)
    return call


async def record_failed_call(
    session: AsyncSession,
    *,
    user_id: int,
    kind: AiCallKind,
    model: str,
    error: str,
    goal_id: uuid.UUID | None = None,
    latency_ms: int = 0,
) -> AiCall:
    """Провалы пишем тоже: без них не видно, что маршруты не собираются
    у каждого третьего."""
    return await record_ai_call(
        session,
        user_id=user_id,
        kind=kind,
        model=model,
        usage=TokenUsage(),
        latency_ms=latency_ms,
        goal_id=goal_id,
        ok=False,
        error=error,
    )
