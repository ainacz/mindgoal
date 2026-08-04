"""О чём спрашивать по итогу дня.

Revision ID: 0003_result_prompt
Revises: 0002_result_note
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0003_result_prompt"
down_revision: str | None = "0002_result_note"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "daily_tasks", sa.Column("result_prompt", sa.String(length=60), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("daily_tasks", "result_prompt")
