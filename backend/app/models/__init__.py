"""Реэкспорт моделей.

Alembic импортирует только этот модуль — значит все таблицы должны быть
зарегистрированы в metadata здесь, иначе автогенерация их не увидит.
"""

from app.enums import AiCallKind, GoalStatus
from app.models.ai_call import AiCall
from app.models.base import Base
from app.models.checklist_item import TaskChecklistItem
from app.models.criterion import GoalCriterion
from app.models.daily_task import DailyTask
from app.models.goal import Goal
from app.models.phase import Phase
from app.models.user import User

__all__ = [
    "AiCall",
    "AiCallKind",
    "Base",
    "DailyTask",
    "Goal",
    "GoalCriterion",
    "GoalStatus",
    "Phase",
    "TaskChecklistItem",
    "User",
]
