"""Контракты с моделью — единственное место, где мы не доверяем входу.

Эти тесты не ходят в сеть и не поднимают базу: проверяем ровно то,
что схема ловит кривой ответ до записи в БД.
"""

import pytest
from pydantic import ValidationError

from app.schemas.ai import (
    AIClarifyResult,
    AICriteriaResult,
    AIDayBatch,
    AIRouteSkeleton,
)


def _day(n: int, minutes: int = 30) -> dict:
    return {
        "day_number": n,
        "title": f"Задача дня {n}",
        "estimated_minutes": minutes,
        "description": "Достаточно длинное описание того, что надо сделать.",
        "hint": None,
        "checklist": ["первый пункт"],
    }


# --------------------------------------------------------------- уточнение


def test_clarify_always_asks_about_starting_point():
    """Вопросы задаются даже для конкретной цели: без точки старта
    маршрут одинаков у новичка и у продолжающего."""
    result = AIClarifyResult.model_validate(
        {"questions": [{"question": "Какой уровень сейчас?", "options": ["Ноль", "Средний"]}]}
    )
    assert len(result.questions) == 1


def test_clarify_rejects_empty_questions():
    with pytest.raises(ValidationError):
        AIClarifyResult.model_validate({"questions": []})


def test_clarify_rejects_leftover_field():
    """Модель иногда цепляется за старую форму ответа — ловим это здесь,
    а не в проде."""
    with pytest.raises(ValidationError):
        AIClarifyResult.model_validate(
            {
                "needs_clarification": False,
                "questions": [{"question": "Сколько времени есть?", "options": ["15", "30"]}],
            }
        )


# --------------------------------------------------------------- критерии


def test_criteria_accepts_measurable():
    result = AICriteriaResult.model_validate(
        {
            "category": "Карьера",
            "criteria": [
                "Задеплоен сервис с публичной ссылкой",
                "На GitHub три репозитория с README",
                "Пройдено два технических собеседования",
            ],
        }
    )
    assert len(result.criteria) == 3


def test_criteria_rejects_state_of_mind():
    with pytest.raises(ValidationError):
        AICriteriaResult.model_validate(
            {
                "category": "Карьера",
                "criteria": [
                    "Задеплоен сервис с публичной ссылкой",
                    "Разобрался с векторными базами",
                    "Пройдено два собеседования",
                ],
            }
        )


def test_criteria_rejects_wrong_count():
    with pytest.raises(ValidationError):
        AICriteriaResult.model_validate(
            {"category": "Карьера", "criteria": ["Задеплоен сервис"]}
        )


# --------------------------------------------------------------- скелет


def test_skeleton_valid():
    skeleton = AIRouteSkeleton.model_validate(
        {
            "phases": [
                {"title": "База", "start_day": 1, "end_day": 30},
                {"title": "RAG", "start_day": 31, "end_day": 60},
                {"title": "Агенты", "start_day": 61, "end_day": 90},
            ],
            "days": [_day(1, 15), _day(2), _day(3)],
        }
    )
    assert len(skeleton.days) == 3


def test_skeleton_rejects_gap_between_phases():
    with pytest.raises(ValidationError):
        AIRouteSkeleton.model_validate(
            {
                "phases": [
                    {"title": "База", "start_day": 1, "end_day": 30},
                    {"title": "RAG", "start_day": 35, "end_day": 60},
                ],
                "days": [_day(1, 15)],
            }
        )


def test_skeleton_rejects_phases_not_starting_at_one():
    with pytest.raises(ValidationError):
        AIRouteSkeleton.model_validate(
            {
                "phases": [{"title": "База", "start_day": 2, "end_day": 30}],
                "days": [_day(1, 15)],
            }
        )


def test_skeleton_rejects_long_first_day():
    """Первый день — 15 минут физического действия. Это правило продукта."""
    with pytest.raises(ValidationError):
        AIRouteSkeleton.model_validate(
            {
                "phases": [{"title": "База", "start_day": 1, "end_day": 30}],
                "days": [_day(1, 45)],
            }
        )


def test_skeleton_rejects_non_sequential_days():
    with pytest.raises(ValidationError):
        AIRouteSkeleton.model_validate(
            {
                "phases": [{"title": "База", "start_day": 1, "end_day": 30}],
                "days": [_day(1, 15), _day(3)],
            }
        )


def test_skeleton_rejects_unknown_field():
    """Строгость схемы: лишнее поле — это провал вызова, а не сюрприз в базе."""
    with pytest.raises(ValidationError):
        AIRouteSkeleton.model_validate(
            {
                "phases": [{"title": "База", "start_day": 1, "end_day": 30}],
                "days": [_day(1, 15)],
                "summary": "маршрут готов",
            }
        )


# --------------------------------------------------------------- батч


def test_batch_valid():
    batch = AIDayBatch.model_validate({"days": [_day(n) for n in range(8, 15)]})
    assert batch.days[0].day_number == 8


def test_batch_rejects_duplicates():
    with pytest.raises(ValidationError):
        AIDayBatch.model_validate({"days": [_day(8), _day(8)]})
