"""Схемы дня и чек-листа."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class ChecklistItemOut(ORMModel):
    id: uuid.UUID
    text: str
    is_done: bool
    order_index: int


class ChecklistItemUpdate(BaseModel):
    is_done: bool


class CompleteDayRequest(BaseModel):
    """Запись результата едет вместе с завершением дня.

    Отдельного «сохранить» нет намеренно: человек записывает итог,
    когда день закончен, а не в процессе. Цена решения — если закрыть
    приложение, не нажав «Завершить день», набранное пропадёт.

    Приходит только с тех дней, у которых есть result_prompt.
    """

    result_note: str | None = None


class DailyTaskOut(ORMModel):
    id: uuid.UUID
    day_number: int
    title: str
    estimated_minutes: int
    description: str
    hint: str | None
    result_prompt: str | None
    result_note: str | None
    is_completed: bool
    completed_at: datetime | None
    is_simplified: bool
    checklist: list[ChecklistItemOut]


class TodayOut(ORMModel):
    """Экран «Сегодня».

    task пустой означает, что человек упёрся в край написанного маршрута:
    фронт показывает «дописываю следующие дни» и кнопку повтора.
    """

    goal_id: uuid.UUID
    goal_title: str
    current_day: int
    duration_days: int
    streak_days: int
    total_xp: int
    phase_title: str | None
    task: DailyTaskOut | None


class CompleteDayOut(ORMModel):
    """Что вернуть после завершения дня, чтобы фронт не ходил ещё раз."""

    current_day: int
    streak_days: int
    total_xp: int
    xp_earned: int
    goal_completed: bool
