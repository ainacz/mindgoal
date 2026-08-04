"""Клиент DeepSeek.

Знает ровно две вещи: как сходить в chat/completions и как достать оттуда
текст и статистику токенов. Ни схем, ни промптов, ни базы здесь нет —
поэтому его легко подменить фейком в тестах.
"""

import time
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.ai.errors import AITransportError
from app.schemas.ai import TokenUsage

Message = dict[str, str]


@dataclass(slots=True)
class Completion:
    content: str
    usage: TokenUsage
    model: str
    latency_ms: int


class LLMClient(Protocol):
    """То, что нужно механикам. Больше от клиента ничего не требуется."""

    async def complete(
        self, messages: list[Message], *, max_tokens: int, temperature: float
    ) -> Completion: ...


class DeepSeekClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
        timeout: float = 90.0,
    ) -> None:
        self._model = model
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout, connect=10.0),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    async def complete(
        self, messages: list[Message], *, max_tokens: int, temperature: float
    ) -> Completion:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            # JSON mode. Слово «json» обязано присутствовать в промпте,
            # иначе провайдер отклоняет запрос — оно есть в каждом системном.
            "response_format": {"type": "json_object"},
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        started = time.perf_counter()
        try:
            response = await self._client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:400]
            raise AITransportError(
                f"DeepSeek ответил {exc.response.status_code}: {body}"
            ) from exc
        except httpx.HTTPError as exc:
            raise AITransportError(f"Не удалось дойти до DeepSeek: {exc}") from exc
        except ValueError as exc:
            raise AITransportError("DeepSeek вернул не JSON") from exc

        latency_ms = int((time.perf_counter() - started) * 1000)

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AITransportError(f"Неожиданная форма ответа: {data!r:.300}") from exc

        # Обрыв по потолку токенов — не «кривой JSON», а недоделанная работа.
        # Отличаем явно, иначе ретрай упрётся в тот же потолок.
        finish_reason = data["choices"][0].get("finish_reason")
        if finish_reason == "length":
            raise AITransportError(
                f"Ответ обрезан по max_tokens={max_tokens}. "
                "Нужен батч поменьше или потолок повыше."
            )

        return Completion(
            content=content,
            usage=TokenUsage.model_validate(data.get("usage") or {}),
            model=data.get("model", self._model),
            latency_ms=latency_ms,
        )

    async def aclose(self) -> None:
        await self._client.aclose()
