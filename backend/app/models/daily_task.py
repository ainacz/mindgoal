"""Задача одного дня. Ровно одна на день маршрута."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, uuid_pk

if TYPE_CHECKING:
    from app.models.checklist_item import TaskChecklistItem
    from app.models.goal import Goal


class DailyTask(Base):
    __tablename__ = "daily_tasks"
    __table_args__ = (
        # Ключевая гарантия: один день маршрута — одна задача.
        # Без неё повторный батч продублирует дни при ретрае.
        UniqueConstraint("goal_id", "day_number", name="one_task_per_day"),
        CheckConstraint("day_number >= 1", name="day_number_positive"),
        CheckConstraint(
            "estimated_minutes BETWEEN 5 AND 240", name="estimated_minutes_sane"
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    goal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True
    )

    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    hint: Mapped[str | None] = mapped_column(Text)

    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Задачу переписали под «мало времени». Флаг нужен, чтобы не предлагать
    # упрощение дважды и чтобы видеть в аналитике, что упрощают чаще всего.
    is_simplified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    goal: Mapped["Goal"] = relationship(back_populates="tasks")
    checklist: Mapped[list["TaskChecklistItem"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TaskChecklistItem.order_index",
    )

    def __repr__(self) -> str:
        return f"<DailyTask день {self.day_number}: {self.title[:32]!r}>"
