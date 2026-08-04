"""Поле для записи результата дня.

Revision ID: 0002_result_note
Revises: 0001_initial
Create Date: 2026-08-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_result_note"
down_revision: str | None = "0001_initial"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("daily_tasks", sa.Column("result_note", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("daily_tasks", "result_note")
