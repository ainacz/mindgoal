"""Фаза — крупный отрезок маршрута. Делит дни и даёт им смысл."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, uuid_pk

if TYPE_CHECKING:
    from app.models.goal import Goal


class Phase(Base):
    __tablename__ = "phases"
    __table_args__ = (
        CheckConstraint("end_day >= start_day", name="phase_range_valid"),
        CheckConstraint("start_day >= 1", name="phase_start_positive"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    goal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(120), nullable=False)
    start_day: Mapped[int] = mapped_column(Integer, nullable=False)
    end_day: Mapped[int] = mapped_column(Integer, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    goal: Mapped["Goal"] = relationship(back_populates="phases")

    def contains(self, day_number: int) -> bool:
        return self.start_day <= day_number <= self.end_day

    def __repr__(self) -> str:
        return f"<Phase {self.title!r} {self.start_day}—{self.end_day}>"
