"""Журнал обращений к модели.

Нужен ровно для двух вещей: видеть, куда уходят токены, и убеждаться,
что кэш работает. Если cached_tokens держится на нуле — значит системный
промпт где-то плавает между запросами, и вход стоит в пятьдесят раз дороже,
чем мог бы.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import AiCallKind
from app.models.base import Base, created_at_column, uuid_pk


class AiCall(Base):
    __tablename__ = "ai_calls"
    __table_args__ = (Index("ix_ai_calls_user_created", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = uuid_pk()

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Пусто у вызовов, которые случились до создания цели (уточнение, критерии).
    goal_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("goals.id", ondelete="CASCADE")
    )

    kind: Mapped[AiCallKind] = mapped_column(
        SAEnum(AiCallKind, name="ai_call_kind", native_enum=True), nullable=False
    )
    model: Mapped[str] = mapped_column(String(64), nullable=False)

    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Сколько входных токенов попало в кэш — из prompt_cache_hit_tokens в ответе API.
    cached_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ok: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = created_at_column()

    def __repr__(self) -> str:
        return (
            f"<AiCall {self.kind.value} in={self.prompt_tokens} "
            f"cached={self.cached_tokens} out={self.completion_tokens}>"
        )
