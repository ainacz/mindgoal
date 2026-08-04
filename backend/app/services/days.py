"""День: показать текущий, отметить пункт, завершить."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.client import LLMClient
from app.ai.mechanics import simplify_task
from app.config import Settings
from app.enums import AiCallKind
from app.models import DailyTask, Goal, TaskChecklistItem, User
from app.schemas.task import CompleteDayOut, DailyTaskOut, TodayOut
from app.services.ai_usage import record_ai_call
from app.services.goals import complete_goal_if_finished
from app.services.streak import local_today, next_streak

logger = logging.getLogger(__name__)


class DayError(Exception):
    """Попытка закрыть не тот день или закрыть дважды."""


async def get_task(
    session: AsyncSession, goal: Goal, day_number: int
) -> DailyTask | None:
    return await session.scalar(
        select(DailyTask)
        .where(DailyTask.goal_id == goal.id, DailyTask.day_number == day_number)
        .options(selectinload(DailyTask.checklist))
    )


async def find_goal_by_task(
    session: AsyncSession, user: User, task_id: uuid.UUID
) -> tuple[Goal, DailyTask] | None:
    """Цель и задача по id задачи, сразу с проверкой владельца.

    Одним запросом, потому что роутеру нужно и то и другое, а два
    похода в базу ради этого — лишние.
    """
    row = await session.execute(
        select(Goal, DailyTask)
        .join(DailyTask, DailyTask.goal_id == Goal.id)
        .where(DailyTask.id == task_id, Goal.user_id == user.id)
        .options(selectinload(Goal.phases), selectinload(DailyTask.checklist))
    )
    result = row.first()
    return (result[0], result[1]) if result else None


async def build_today(
    session: AsyncSession, user: User, goal: Goal
) -> TodayOut:
    """Экран «Сегодня».

    Пустой task — не ошибка: человек упёрся в край написанного маршрута.
    Фронт покажет «дописываю следующие дни» и кнопку повтора.
    """
    task = await get_task(session, goal, goal.current_day)
    phase = next((p for p in goal.phases if p.contains(goal.current_day)), None)
    return TodayOut(
        goal_id=goal.id,
        goal_title=goal.title,
        current_day=goal.current_day,
        duration_days=goal.duration_days,
        streak_days=goal.streak_days,
        total_xp=user.total_xp,
        phase_title=phase.title if phase else None,
        task=DailyTaskOut.model_validate(task) if task else None,
    )


async def toggle_checklist_item(
    session: AsyncSession, user: User, item_id: uuid.UUID, is_done: bool
) -> TaskChecklistItem:
    """Пункт ищем сразу с проверкой владельца: иначе по прямой ссылке
    можно было бы отмечать чужие чек-листы."""
    item = await session.scalar(
        select(TaskChecklistItem)
        .join(DailyTask, TaskChecklistItem.daily_task_id == DailyTask.id)
        .join(Goal, DailyTask.goal_id == Goal.id)
        .where(TaskChecklistItem.id == item_id, Goal.user_id == user.id)
    )
    if item is None:
        raise DayError("Пункт не найден")
    item.is_done = is_done
    await session.flush()
    return item


async def simplify_day(
    session: AsyncSession,
    client: LLMClient,
    settings: Settings,
    *,
    user: User,
    goal: Goal,
    task: DailyTask,
) -> DailyTask:
    """«Мало времени»: переписать день под пятнадцать минут с телефона.

    Задача перезаписывается на месте, старая версия не хранится: человек
    нажал это, потому что сегодня не сможет сделать исходную, и вернуть
    её ему всё равно некуда. Флаг is_simplified не даёт нажать дважды.
    """
    if task.is_completed:
        raise DayError("День уже закрыт")
    if task.is_simplified:
        raise DayError("День уже упрощён")

    result = await simplify_task(
        client,
        settings,
        goal_title=goal.title,
        day_number=task.day_number,
        task_title=task.title,
        task_description=task.description,
    )
    day = result.data

    task.title = day.title
    task.estimated_minutes = day.estimated_minutes
    task.description = day.description
    task.hint = day.hint
    task.is_simplified = True

    # Чек-лист меняется целиком: пункты старой задачи к новой не относятся.
    for item in list(task.checklist):
        await session.delete(item)
    task.checklist = [
        TaskChecklistItem(text=text, order_index=index)
        for index, text in enumerate(day.checklist)
    ]
    await session.flush()

    await record_ai_call(
        session,
        user_id=user.id,
        goal_id=goal.id,
        kind=AiCallKind.simplify,
        model=result.model,
        usage=result.usage,
        latency_ms=result.latency_ms,
    )
    return task


async def complete_day(
    session: AsyncSession,
    settings: Settings,
    *,
    user: User,
    goal: Goal,
    task: DailyTask,
    result_note: str | None = None,
) -> CompleteDayOut:
    """Завершить текущий день.

    Закрыть можно только тот день, на котором человек стоит: иначе
    двойное нажатие или старая вкладка перепрыгнули бы маршрут вперёд.
    """
    if task.goal_id != goal.id:
        raise DayError("Задача не из этой цели")
    if task.day_number != goal.current_day:
        raise DayError("Закрыть можно только текущий день")
    if task.is_completed:
        raise DayError("День уже закрыт")

    task.is_completed = True
    task.completed_at = datetime.now(timezone.utc)
    if result_note and result_note.strip():
        task.result_note = result_note.strip()[:1000]

    today = local_today(user.tz_offset_minutes)
    goal.streak_days = next_streak(goal.last_completed_date, goal.streak_days, today)
    goal.last_completed_date = today

    user.total_xp += settings.xp_per_day
    goal.current_day += 1
    finished = await complete_goal_if_finished(goal)

    await session.flush()
    logger.info(
        "Цель %s: закрыт день %s, стрик %s", goal.id, task.day_number, goal.streak_days
    )

    return CompleteDayOut(
        current_day=goal.current_day,
        streak_days=goal.streak_days,
        total_xp=user.total_xp,
        xp_earned=settings.xp_per_day,
        goal_completed=finished,
    )
