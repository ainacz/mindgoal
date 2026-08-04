"""Цель — корень всего маршрута."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import GoalStatus
from app.models.base import Base, created_at_column, uuid_pk

if TYPE_CHECKING:
    from app.models.criterion import GoalCriterion
    from app.models.daily_task import DailyTask
    from app.models.phase import Phase
    from app.models.user import User


class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = (
        CheckConstraint(
            "duration_days IN (30, 60, 90)", name="duration_days_allowed"
        ),
        CheckConstraint("current_day >= 1", name="current_day_positive"),
        CheckConstraint(
            "generated_until_day >= 0", name="generated_until_day_non_negative"
        ),
        Index("ix_goals_user_status", "user_id", "status"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # Короткая метка от ИИ для карточки: «Карьера», «Бизнес», «Язык».
    category: Mapped[str | None] = mapped_column(String(40))

    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)

    # День, на котором человек стоит сейчас. Двигается только завершением дня —
    # календарь на него не влияет.
    current_day: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # До какого дня маршрут уже написан. Всё, что дальше, — заперто.
    generated_until_day: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    status: Mapped[GoalStatus] = mapped_column(
        SAEnum(GoalStatus, name="goal_status", native_enum=True),
        default=GoalStatus.draft,
        nullable=False,
    )

    # Стрик живёт на цели, а не на пользователе: в интерфейсе он стоит
    # рядом с каждой целью, значит ей и принадлежит.
    streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_completed_date: Mapped[date | None] = mapped_column(Date)

    created_at: Mapped[datetime] = created_at_column()
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="goals")
    criteria: Mapped[list["GoalCriterion"]] = relationship(
        back_populates="goal",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="GoalCriterion.order_index",
    )
    phases: Mapped[list["Phase"]] = relationship(
        back_populates="goal",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Phase.order_index",
    )
    tasks: Mapped[list["DailyTask"]] = relationship(
        back_populates="goal",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="DailyTask.day_number",
    )

    def needs_more_days(self, threshold: int) -> bool:
        """Пора ли дописывать следующий батч.

        threshold приходит из настроек, чтобы модель не тянула конфиг.
        """
        if self.generated_until_day >= self.duration_days:
            return False
        return self.current_day > self.generated_until_day - threshold

    def __repr__(self) -> str:
        return f"<Goal {self.id} «{self.title}» {self.current_day}/{self.duration_days}>"
