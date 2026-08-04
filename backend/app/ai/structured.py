"""Получение структурированного ответа: вызов, разбор, проверка, один ретрай.

Здесь собрана вся логика «переспросить». Механики её не дублируют —
они только называют схему, промпт и потолок токенов.
"""

import json
import logging
from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

from app.ai.client import Completion, LLMClient, Message
from app.ai.errors import AIInvalidResponse
from app.schemas.ai import TokenUsage

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


@dataclass(slots=True)
class Structured(Generic[T]):
    """Результат вместе с расходом: расход нужен вызывающему,
    чтобы записать AiCall, а слой ИИ в базу не ходит."""

    data: T
    usage: TokenUsage
    model: str
    latency_ms: int
    attempts: int


def _parse(raw: str, schema: type[T]) -> T:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AIInvalidResponse(f"это не json: {exc}", raw=raw) from exc

    if not isinstance(payload, dict):
        raise AIInvalidResponse("на верхнем уровне ожидался объект", raw=raw)

    try:
        return schema.model_validate(payload)
    except ValidationError as exc:
        # Модели отдаём человекочитаемую претензию, а не дамп pydantic:
        # по короткому списку «поле — что не так» она чинит точнее.
        problems = "; ".join(
            f"{'.'.join(str(p) for p in err['loc']) or 'корень'}: {err['msg']}"
            for err in exc.errors()[:5]
        )
        raise AIInvalidResponse(problems, raw=raw) from exc


async def generate_structured(
    client: LLMClient,
    schema: type[T],
    *,
    system: str,
    user: str,
    max_tokens: int,
    temperature: float,
) -> Structured[T]:
    """Один повтор, не больше.

    Если модель дважды не смогла ответить по контракту — это не та ситуация,
    которую чинит третья попытка. Дальше пусть решает вызывающий: показать
    человеку кнопку «попробовать ещё раз» или отложить батч до следующего
    захода.
    """
    messages: list[Message] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    first_failure: AIInvalidResponse | None = None

    for attempt in (1, 2):
        completion: Completion = await client.complete(
            messages, max_tokens=max_tokens, temperature=temperature
        )
        try:
            data = _parse(completion.content, schema)
        except AIInvalidResponse as exc:
            if attempt == 2:
                logger.warning(
                    "Схема %s не собралась дважды: %s", schema.__name__, exc.reason
                )
                raise
            first_failure = exc
            logger.info(
                "Схема %s не собралась, переспрашиваю: %s",
                schema.__name__,
                exc.reason,
            )
            # Системный промпт не трогаем — иначе потеряем кэш префикса.
            messages = [
                *messages,
                {"role": "assistant", "content": completion.content},
                {
                    "role": "user",
                    "content": (
                        "Предыдущий ответ не прошёл проверку: "
                        f"{exc.reason}. Пришли исправленный json той же формы, "
                        "без пояснений."
                    ),
                },
            ]
            continue

        if attempt == 2 and first_failure is not None:
            logger.info("Схема %s собралась со второго раза", schema.__name__)

        return Structured(
            data=data,
            usage=completion.usage,
            model=completion.model,
            latency_ms=completion.latency_ms,
            attempts=attempt,
        )

    raise AssertionError("недостижимо")
