"""Жизненный цикл цели: уточнение, критерии, скелет, догенерация, удаление."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.client import LLMClient
from app.ai.mechanics import clarify_goal, make_batch, make_criteria, make_skeleton
from app.config import Settings
from app.enums import AiCallKind, GoalStatus
from app.models import DailyTask, Goal, GoalCriterion, Phase, TaskChecklistItem, User
from app.schemas.ai import AIDay
from app.schemas.goal import ClarifyAnswer, ClarifyQuestion, GoalCreate
from app.services.ai_usage import record_ai_call

logger = logging.getLogger(__name__)


class GoalError(Exception):
    """Нарушение правил цели: не тот статус, чужая цель, нечего генерировать."""


def _answers(items: list[ClarifyAnswer]) -> list[tuple[str, str]]:
    return [(a.question, a.answer) for a in items]


# --------------------------------------------------------------- уточнение


async def ask_clarifying_questions(
    session: AsyncSession,
    client: LLMClient,
    settings: Settings,
    *,
    user: User,
    title: str,
    duration_days: int,
) -> list[ClarifyQuestion]:
    result = await clarify_goal(
        client, settings, title=title, duration_days=duration_days
    )
    await record_ai_call(
        session,
        user_id=user.id,
        kind=AiCallKind.clarify,
        model=result.model,
        usage=result.usage,
        latency_ms=result.latency_ms,
    )
    return [
        ClarifyQuestion(question=q.question, options=q.options)
        for q in result.data.questions
    ]


# --------------------------------------------------------------- создание


async def create_goal(
    session: AsyncSession,
    client: LLMClient,
    settings: Settings,
    *,
    user: User,
    payload: GoalCreate,
) -> Goal:
    """Заводит цель в статусе draft вместе с критериями.

    Маршрута ещё нет: человек сначала смотрит критерии и правит их,
    и только потом жмёт «Собрать маршрут». Генерировать до подтверждения —
    значит выбрасывать сгенерированное каждый раз, когда критерий не тот.
    """
    result = await make_criteria(
        client,
        settings,
        title=payload.title,
        duration_days=payload.duration_days,
        answers=_answers(payload.answers),
    )

    goal = Goal(
        user_id=user.id,
        title=payload.title,
        category=result.data.category,
        duration_days=payload.duration_days,
        status=GoalStatus.draft,
    )
    goal.criteria = [
        GoalCriterion(text=text, order_index=index)
        for index, text in enumerate(result.data.criteria)
    ]
    session.add(goal)
    await session.flush()

    await record_ai_call(
        session,
        user_id=user.id,
        goal_id=goal.id,
        kind=AiCallKind.criteria,
        model=result.model,
        usage=result.usage,
        latency_ms=result.latency_ms,
    )
    return goal


async def replace_criteria(
    session: AsyncSession, goal: Goal, texts: list[str]
) -> Goal:
    if goal.status is not GoalStatus.draft:
        raise GoalError("Критерии правятся только до сборки маршрута")

    for criterion in list(goal.criteria):
        await session.delete(criterion)
    goal.criteria = [
        GoalCriterion(goal_id=goal.id, text=text, order_index=index)
        for index, text in enumerate(texts)
    ]
    await session.flush()
    return goal


# --------------------------------------------------------------- генерация


def _build_task(goal_id: uuid.UUID, day: AIDay) -> DailyTask:
    task = DailyTask(
        goal_id=goal_id,
        day_number=day.day_number,
        title=day.title,
        estimated_minutes=day.estimated_minutes,
        description=day.description,
        hint=day.hint,
    )
    task.checklist = [
        TaskChecklistItem(text=text, order_index=index)
        for index, text in enumerate(day.checklist)
    ]
    return task


async def generate_skeleton(
    session: AsyncSession,
    client: LLMClient,
    settings: Settings,
    *,
    user: User,
    goal: Goal,
    answers: list[ClarifyAnswer] | None = None,
) -> Goal:
    """Фазы на весь срок и первая неделя дней.

    Статус переводится в active только после того, как всё записано:
    цель, у которой status=active и ноль дней, — это цель, из которой
    человек не сможет выйти.
    """
    if goal.status is not GoalStatus.draft:
        raise GoalError("Маршрут уже собран")

    goal.status = GoalStatus.generating
    await session.flush()

    result = await make_skeleton(
        client,
        settings,
        title=goal.title,
        duration_days=goal.duration_days,
        criteria=[c.text for c in goal.criteria],
        # Точка старта человека. Без неё маршрут для того, кто бегает
        # пять километров, и для того, кто не бегает вовсе, одинаковый.
        answers=_answers(answers or []),
    )

    goal.phases = [
        Phase(
            title=phase.title,
            start_day=phase.start_day,
            end_day=phase.end_day,
            order_index=index,
        )
        for index, phase in enumerate(
            sorted(result.data.phases, key=lambda p: p.start_day)
        )
    ]
    for day in result.data.days:
        session.add(_build_task(goal.id, day))

    goal.generated_until_day = max(d.day_number for d in result.data.days)
    goal.current_day = 1
    goal.status = GoalStatus.active
    await session.flush()

    await record_ai_call(
        session,
        user_id=user.id,
        goal_id=goal.id,
        kind=AiCallKind.skeleton,
        model=result.model,
        usage=result.usage,
        latency_ms=result.latency_ms,
    )
    return goal


async def ensure_days(
    session: AsyncSession,
    client: LLMClient,
    settings: Settings,
    *,
    user: User,
    goal: Goal,
) -> int:
    """Дописать следующий батч, если пора. Возвращает число новых дней.

    Идемпотентна: generated_until_day двигается только после успешной
    записи, а дни, которые уже есть, пропускаются. Поэтому упавший
    посреди работы батч можно спокойно повторить — дубликатов не будет,
    да и уникальность (goal_id, day_number) не даст.
    """
    if goal.status is not GoalStatus.active:
        return 0
    if not goal.needs_more_days(settings.generate_ahead_threshold):
        return 0

    first = goal.generated_until_day + 1
    last = min(first + settings.batch_size_days - 1, goal.duration_days)
    if first > last:
        return 0

    phase = next(
        (p for p in goal.phases if p.contains(first)),
        goal.phases[-1] if goal.phases else None,
    )

    written = await session.scalars(
        select(DailyTask.title)
        .where(DailyTask.goal_id == goal.id)
        .order_by(DailyTask.day_number)
    )

    result = await make_batch(
        client,
        settings,
        title=goal.title,
        duration_days=goal.duration_days,
        criteria=[c.text for c in goal.criteria],
        current_phase=phase.title if phase else "",
        written_titles=list(written),
        first_day=first,
        last_day=last,
    )

    existing = set(
        await session.scalars(
            select(DailyTask.day_number).where(DailyTask.goal_id == goal.id)
        )
    )
    added = 0
    for day in result.data.days:
        if day.day_number in existing or day.day_number > goal.duration_days:
            continue
        session.add(_build_task(goal.id, day))
        added += 1

    if added:
        goal.generated_until_day = max(
            goal.generated_until_day,
            max(d.day_number for d in result.data.days if d.day_number <= goal.duration_days),
        )
    await session.flush()

    await record_ai_call(
        session,
        user_id=user.id,
        goal_id=goal.id,
        kind=AiCallKind.batch,
        model=result.model,
        usage=result.usage,
        latency_ms=result.latency_ms,
    )
    logger.info("Цель %s: дописано дней %s (%s—%s)", goal.id, added, first, last)
    return added


# --------------------------------------------------------------- выборки


async def list_goals(session: AsyncSession, user: User) -> list[Goal]:
    result = await session.scalars(
        select(Goal)
        .where(Goal.user_id == user.id, Goal.status != GoalStatus.archived)
        .order_by(Goal.created_at.desc())
    )
    return list(result)


async def get_goal(
    session: AsyncSession, user: User, goal_id: uuid.UUID, *, full: bool = False
) -> Goal | None:
    query = select(Goal).where(Goal.id == goal_id, Goal.user_id == user.id)
    if full:
        # Ленивая подгрузка в асинхронном движке падает — грузим явно.
        query = query.options(
            selectinload(Goal.criteria),
            selectinload(Goal.phases),
            selectinload(Goal.tasks).selectinload(DailyTask.checklist),
        )
    else:
        query = query.options(selectinload(Goal.criteria), selectinload(Goal.phases))
    return await session.scalar(query)


async def delete_goal(session: AsyncSession, goal: Goal) -> None:
    """Удаляем по-настоящему. Мягкое удаление здесь было бы враньём:
    человек нажал «Удалить» с подтверждением и ждёт, что цель исчезла."""
    await session.delete(goal)


async def complete_goal_if_finished(goal: Goal) -> bool:
    if goal.current_day > goal.duration_days:
        goal.status = GoalStatus.completed
        goal.completed_at = datetime.now(timezone.utc)
        return True
    return False
