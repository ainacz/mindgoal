"""Пользователь. Заводится при первом валидном initData."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at_column

if TYPE_CHECKING:
    from app.models.goal import Goal


class User(Base):
    __tablename__ = "users"

    # id пользователя в Telegram. Своего суррогатного ключа не заводим:
    # telegram_id уникален, стабилен и приходит в каждом запросе.
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)

    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(128))

    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Смещение часового пояса в минутах, присылает фронт.
    # Нужно, чтобы «сегодня» для стрика считалось по местному времени человека.
    tz_offset_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = created_at_column()

    goals: Mapped[list["Goal"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User {self.id} @{self.username}>"
