"""Общие базовые схемы."""

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Схема, которую собирают из объекта SQLAlchemy."""

    model_config = ConfigDict(from_attributes=True)


class StrictModel(BaseModel):
    """Схема для ответа модели.

    extra='forbid' здесь принципиален: если DeepSeek придумал лишнее поле
    или переименовал существующее — мы узнаём об этом сразу и уходим в ретрай,
    а не сохраняем в базу полупустой маршрут.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
