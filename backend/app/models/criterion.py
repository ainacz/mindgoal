"""Критерий готовности — то, что можно предъявить."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, uuid_pk

if TYPE_CHECKING:
    from app.models.goal import Goal


class GoalCriterion(Base):
    __tablename__ = "goal_criteria"

    id: Mapped[uuid.UUID] = uuid_pk()
    goal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True
    )

    text: Mapped[str] = mapped_column(String(300), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    goal: Mapped["Goal"] = relationship(back_populates="criteria")

    def __repr__(self) -> str:
        return f"<Criterion {self.text[:32]!r}>"
