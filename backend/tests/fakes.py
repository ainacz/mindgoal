"""Фейковый клиент модели.

Отдаёт заранее заготовленные ответы по очереди и запоминает, что ему
прислали. Этого хватает, чтобы проверить и разбор, и ретрай, и то,
что системный промпт не меняется между попытками.
"""

import json
from typing import Any

from app.ai.client import Completion, Message
from app.ai.errors import AITransportError
from app.schemas.ai import TokenUsage


class FakeLLMClient:
    def __init__(self, responses: list[str | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[list[Message]] = []
        self.max_tokens_seen: list[int] = []

    @staticmethod
    def json_response(payload: Any) -> str:
        return json.dumps(payload, ensure_ascii=False)

    async def complete(
        self, messages: list[Message], *, max_tokens: int, temperature: float
    ) -> Completion:
        if not self._responses:
            raise AssertionError("Фейку не оставили ответов, а его вызвали снова")

        self.calls.append([dict(m) for m in messages])
        self.max_tokens_seen.append(max_tokens)

        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item

        return Completion(
            content=item,
            usage=TokenUsage(
                prompt_tokens=1000,
                completion_tokens=500,
                prompt_cache_hit_tokens=768,
                prompt_cache_miss_tokens=232,
                total_tokens=1500,
            ),
            model="deepseek-chat",
            latency_ms=1234,
        )

    # --- то, что удобно спрашивать в тестах ---

    @property
    def system_prompts(self) -> list[str]:
        return [m[0]["content"] for m in self.calls]

    @property
    def call_count(self) -> int:
        return len(self.calls)


def transport_error(message: str = "сеть отвалилась") -> AITransportError:
    return AITransportError(message)
