"""Схемы цели: создание, уточнение, критерии, выдача."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.enums import GoalStatus
from app.schemas.common import ORMModel
from app.schemas.task import DailyTaskOut

ALLOWED_DURATIONS = (30, 60, 90)


def _check_duration(value: int) -> int:
    if value not in ALLOWED_DURATIONS:
        raise ValueError(f"Срок должен быть одним из {ALLOWED_DURATIONS}")
    return value


# --------------------------------------------------------------- уточнение


class ClarifyRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    duration_days: int

    _v = field_validator("duration_days")(_check_duration)


class ClarifyQuestion(ORMModel):
    """Вопрос с готовыми вариантами: три касания вместо трёх абзацев."""

    question: str
    options: list[str]


class ClarifyResponse(ORMModel):
    """Пустой список вопросов означает, что цель и так конкретна
    и шаг уточнения надо пропустить."""

    questions: list[ClarifyQuestion]


class ClarifyAnswer(BaseModel):
    question: str = Field(max_length=300)
    answer: str = Field(max_length=200)


# --------------------------------------------------------------- создание


class GoalCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    duration_days: int
    answers: list[ClarifyAnswer] = Field(default_factory=list, max_length=5)

    _v = field_validator("duration_days")(_check_duration)


class GenerateRequest(BaseModel):
    """Ответы про точку старта переезжают с шага уточнения сюда.

    В базе они не хранятся: нужны ровно один раз, при сборке скелета.
    Понадобятся ментору — тогда и заведём колонку.
    """

    answers: list[ClarifyAnswer] = Field(default_factory=list, max_length=5)


class CriterionOut(ORMModel):
    id: uuid.UUID
    text: str
    is_completed: bool
    order_index: int


class CriteriaUpdate(BaseModel):
    """Человек может переписать любой критерий перед генерацией.
    Порядок в списке и есть новый order_index."""

    texts: list[str] = Field(min_length=1, max_length=6)

    @field_validator("texts")
    @classmethod
    def _non_empty(cls, value: list[str]) -> list[str]:
        cleaned = [t.strip() for t in value if t.strip()]
        if not cleaned:
            raise ValueError("Нужен хотя бы один критерий")
        return cleaned


# --------------------------------------------------------------- выдача


class PhaseOut(ORMModel):
    id: uuid.UUID
    title: str
    start_day: int
    end_day: int
    order_index: int


class GoalListItem(ORMModel):
    """Карточка на экране «Мои цели»."""

    id: uuid.UUID
    title: str
    category: str | None
    duration_days: int
    current_day: int
    generated_until_day: int
    status: GoalStatus
    streak_days: int
    created_at: datetime
    completed_at: datetime | None


class GoalDetail(GoalListItem):
    """Цель целиком — для экрана «Карта»."""

    last_completed_date: date | None
    criteria: list[CriterionOut]
    phases: list[PhaseOut]
    tasks: list[DailyTaskOut]


class GoalDraftOut(ORMModel):
    """Ответ на создание цели: сама цель и предложенные критерии."""

    goal: GoalListItem
    criteria: list[CriterionOut]
