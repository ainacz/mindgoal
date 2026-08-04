"""Заглушка модели: приложение проходится целиком без ключа DeepSeek.

Отвечает по тем же контрактам, что и настоящая модель, и генерирует дни
на любой запрошенный диапазон — поэтому маршрут можно пройти от первого
дня до девяностого, не потратив ни цента.

Содержание, разумеется, шаблонное: заглушка проверяет, что работает
приложение, а не что маршруты хорошие. Как появится ключ — достаточно
положить его в .env, код не меняется.
"""

import json
from typing import Any

from app.ai.client import Completion, Message
from app.ai.prompts import (
    SYSTEM_BATCH,
    SYSTEM_CLARIFY,
    SYSTEM_CRITERIA,
    SYSTEM_SIMPLIFY,
    SYSTEM_SKELETON,
)
from app.schemas.ai import TokenUsage

_ACTIONS = (
    "Разобрать один пример и повторить его руками",
    "Написать короткий скрипт и запустить его",
    "Замерить текущий результат и записать число",
    "Собрать три ссылки по теме и выписать тезисы",
    "Сделать один шаг из чек-листа и показать результат",
    "Переписать вчерашнее так, чтобы работало быстрее",
    "Задать вопрос в сообществе и получить ответ",
)


def _wrap(payload: Any) -> Completion:
    """Расход считаем правдоподобным, но нулевым по деньгам:
    в логах будет видно, что вызов был заглушечный."""
    return Completion(
        content=json.dumps(payload, ensure_ascii=False),
        usage=TokenUsage(),
        model="stub",
        latency_ms=15,
    )


def _phases(duration_days: int) -> list[dict]:
    """Три равные фазы, последняя добирает остаток."""
    step = duration_days // 3
    return [
        {"title": "Основа и первые шаги", "start_day": 1, "end_day": step},
        {"title": "Практика и объём", "start_day": step + 1, "end_day": step * 2},
        {"title": "Результат и предъявление", "start_day": step * 2 + 1, "end_day": duration_days},
    ]


def _day(n: int) -> dict:
    if n == 1:
        return {
            "day_number": 1,
            "title": "Поставить всё нужное и сделать одно действие",
            "estimated_minutes": 15,
            "description": "Скачать и установить то, без чего дальше не двинуться, и сразу проверить, что оно запускается.",
            "hint": "Не читай документацию — просто запусти и убедись, что работает.",
            "checklist": ["Установить", "Запустить и убедиться, что работает"],
        }
    return {
        "day_number": n,
        "title": _ACTIONS[n % len(_ACTIONS)],
        "estimated_minutes": 20 + (n % 3) * 10,
        "description": f"Шаг {n}: сделать одно конкретное действие и оставить после себя результат, который можно показать.",
        "hint": None if n % 3 else "Начни с самого мелкого куска — остальное дотянется.",
        "checklist": ["Сделать основное", "Записать, что получилось"],
    }


class StubLLMClient:
    """Тот же интерфейс, что у DeepSeekClient."""

    async def complete(
        self, messages: list[Message], *, max_tokens: int, temperature: float
    ) -> Completion:
        system = messages[0]["content"]
        try:
            payload = json.loads(messages[1]["content"])
        except (IndexError, json.JSONDecodeError):
            payload = {}

        if system == SYSTEM_CLARIFY:
            return self._clarify(payload)
        if system == SYSTEM_CRITERIA:
            return self._criteria()
        if system == SYSTEM_SKELETON:
            return self._skeleton(payload)
        if system == SYSTEM_BATCH:
            return self._batch(payload)
        if system == SYSTEM_SIMPLIFY:
            return self._simplify()

        raise AssertionError("Заглушка не знает этого системного промпта")

    # ------------------------------------------------------------------

    def _clarify(self, payload: dict) -> Completion:
        return _wrap(
            {
                "questions": [
                    {
                        "question": "Какой у тебя сейчас уровень?",
                        "options": ["С нуля", "Кое-что есть", "Уже делаю"],
                    },
                    {
                        "question": "Сколько минут в день есть?",
                        "options": ["15", "30", "60"],
                    },
                    {
                        "question": "Что важнее к концу срока?",
                        "options": ["Результат", "Навык", "Деньги"],
                    },
                ],
            }
        )

    def _criteria(self) -> Completion:
        return _wrap(
            {
                "category": "Проект",
                "criteria": [
                    "Опубликован результат по публичной ссылке",
                    "Собрано три подтверждения от посторонних людей",
                    "Записан итоговый замер в цифрах",
                ],
                "reality_note": None,
            }
        )

    def _skeleton(self, payload: dict) -> Completion:
        duration = int(payload.get("duration_days", 90))
        last = int(payload.get("write_days_to", 7))
        return _wrap(
            {
                "phases": _phases(duration),
                "days": [_day(n) for n in range(1, last + 1)],
            }
        )

    def _batch(self, payload: dict) -> Completion:
        first = int(payload.get("write_days_from", 8))
        last = int(payload.get("write_days_to", first + 6))
        return _wrap({"days": [_day(n) for n in range(first, last + 1)]})

    def _simplify(self) -> Completion:
        return _wrap(
            {
                "title": "Посмотреть разбор и выписать три тезиса",
                "estimated_minutes": 15,
                "description": "С телефона: найти короткий разбор по теме дня и выписать три мысли в заметки.",
                "hint": "Тезисы пиши своими словами, иначе не отложится.",
                "checklist": ["Посмотреть", "Выписать три тезиса"],
            }
        )
