"""Перечисления, общие для моделей и схем.

Живут отдельно, чтобы схемы Pydantic не тянули за собой SQLAlchemy:
слой контрактов должен собираться и тестироваться без базы.
"""

import enum


class GoalStatus(str, enum.Enum):
    """draft      — цель создана, критерии есть, маршрута ещё нет
    generating — идёт генерация скелета
    active     — маршрут пишется и проходится
    completed  — пройден последний день
    archived   — человек убрал цель из активных
    """

    draft = "draft"
    generating = "generating"
    active = "active"
    completed = "completed"
    archived = "archived"


class AiCallKind(str, enum.Enum):
    clarify = "clarify"
    criteria = "criteria"
    skeleton = "skeleton"
    batch = "batch"
    simplify = "simplify"
    mentor = "mentor"
