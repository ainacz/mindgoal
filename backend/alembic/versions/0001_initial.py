"""Начальная схема: пользователи, цели, фазы, дни, чек-лист, журнал вызовов ИИ.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    goal_status = postgresql.ENUM(
        "draft",
        "generating",
        "active",
        "completed",
        "archived",
        name="goal_status",
        create_type=False,
    )
    ai_call_kind = postgresql.ENUM(
        "clarify",
        "criteria",
        "skeleton",
        "batch",
        "simplify",
        "mentor",
        name="ai_call_kind",
        create_type=False,
    )
    goal_status.create(op.get_bind(), checkfirst=True)
    ai_call_kind.create(op.get_bind(), checkfirst=True)

    # ------------------------------------------------------------- users
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("first_name", sa.String(length=128), nullable=True),
        sa.Column("total_xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "tz_offset_minutes", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )

    # ------------------------------------------------------------- goals
    op.create_table(
        "goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=True),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("current_day", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "generated_until_day", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("status", goal_status, nullable=False, server_default="draft"),
        sa.Column("streak_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_completed_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_goals"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_goals_user_id_users",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "duration_days IN (30, 60, 90)", name="ck_goals_duration_days_allowed"
        ),
        sa.CheckConstraint("current_day >= 1", name="ck_goals_current_day_positive"),
        sa.CheckConstraint(
            "generated_until_day >= 0",
            name="ck_goals_generated_until_day_non_negative",
        ),
    )
    op.create_index("ix_goals_user_status", "goals", ["user_id", "status"])

    # ---------------------------------------------------- goal_criteria
    op.create_table(
        "goal_criteria",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("goal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("text", sa.String(length=300), nullable=False),
        sa.Column(
            "is_completed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id", name="pk_goal_criteria"),
        sa.ForeignKeyConstraint(
            ["goal_id"],
            ["goals.id"],
            name="fk_goal_criteria_goal_id_goals",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_goal_criteria_goal_id", "goal_criteria", ["goal_id"])

    # ------------------------------------------------------------ phases
    op.create_table(
        "phases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("goal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("start_day", sa.Integer(), nullable=False),
        sa.Column("end_day", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id", name="pk_phases"),
        sa.ForeignKeyConstraint(
            ["goal_id"], ["goals.id"], name="fk_phases_goal_id_goals", ondelete="CASCADE"
        ),
        sa.CheckConstraint("end_day >= start_day", name="ck_phases_phase_range_valid"),
        sa.CheckConstraint("start_day >= 1", name="ck_phases_phase_start_positive"),
    )
    op.create_index("ix_phases_goal_id", "phases", ["goal_id"])

    # ------------------------------------------------------- daily_tasks
    op.create_table(
        "daily_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("goal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("hint", sa.Text(), nullable=True),
        sa.Column(
            "is_completed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_simplified", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.PrimaryKeyConstraint("id", name="pk_daily_tasks"),
        sa.ForeignKeyConstraint(
            ["goal_id"],
            ["goals.id"],
            name="fk_daily_tasks_goal_id_goals",
            ondelete="CASCADE",
        ),
        # Именно эта уникальность делает повторный батч безопасным.
        sa.UniqueConstraint("goal_id", "day_number", name="one_task_per_day"),
        sa.CheckConstraint("day_number >= 1", name="ck_daily_tasks_day_number_positive"),
        sa.CheckConstraint(
            "estimated_minutes BETWEEN 5 AND 240",
            name="ck_daily_tasks_estimated_minutes_sane",
        ),
    )
    op.create_index("ix_daily_tasks_goal_id", "daily_tasks", ["goal_id"])

    # ----------------------------------------------- task_checklist_items
    op.create_table(
        "task_checklist_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("daily_task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("text", sa.String(length=200), nullable=False),
        sa.Column("is_done", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id", name="pk_task_checklist_items"),
        sa.ForeignKeyConstraint(
            ["daily_task_id"],
            ["daily_tasks.id"],
            name="fk_task_checklist_items_daily_task_id_daily_tasks",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_task_checklist_items_daily_task_id",
        "task_checklist_items",
        ["daily_task_id"],
    )

    # ---------------------------------------------------------- ai_calls
    op.create_table(
        "ai_calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("goal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("kind", ai_call_kind, nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "completion_tokens", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("cached_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ok", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ai_calls"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_ai_calls_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["goal_id"],
            ["goals.id"],
            name="fk_ai_calls_goal_id_goals",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_ai_calls_user_created", "ai_calls", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_ai_calls_user_created", table_name="ai_calls")
    op.drop_table("ai_calls")
    op.drop_index(
        "ix_task_checklist_items_daily_task_id", table_name="task_checklist_items"
    )
    op.drop_table("task_checklist_items")
    op.drop_index("ix_daily_tasks_goal_id", table_name="daily_tasks")
    op.drop_table("daily_tasks")
    op.drop_index("ix_phases_goal_id", table_name="phases")
    op.drop_table("phases")
    op.drop_index("ix_goal_criteria_goal_id", table_name="goal_criteria")
    op.drop_table("goal_criteria")
    op.drop_index("ix_goals_user_status", table_name="goals")
    op.drop_table("goals")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS ai_call_kind")
    op.execute("DROP TYPE IF EXISTS goal_status")
