"""Пункт чек-листа внутри дня."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, uuid_pk

if TYPE_CHECKING:
    from app.models.daily_task import DailyTask


class TaskChecklistItem(Base):
    __tablename__ = "task_checklist_items"

    id: Mapped[uuid.UUID] = uuid_pk()
    daily_task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("daily_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )

    text: Mapped[str] = mapped_column(String(200), nullable=False)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    task: Mapped["DailyTask"] = relationship(back_populates="checklist")

    def __repr__(self) -> str:
        return f"<ChecklistItem {self.text[:32]!r} done={self.is_done}>"
