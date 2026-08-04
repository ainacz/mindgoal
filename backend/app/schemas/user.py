"""Схемы пользователя."""

from pydantic import Field

from app.schemas.common import ORMModel


class SessionRequest(ORMModel):
    """Фронт присылает смещение часового пояса — сам Telegram его не даёт,
    а без него стрик будет считаться по времени сервера."""

    tz_offset_minutes: int = Field(default=0, ge=-14 * 60, le=14 * 60)


class UserOut(ORMModel):
    id: int
    username: str | None
    first_name: str | None
    total_xp: int
