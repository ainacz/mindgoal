"""Эндпоинты. Роутеры тонкие: разобрать вход, позвать сервис, вернуть схему.

Про DeepSeek здесь не знает никто — только про сервисы.
"""

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.api.deps import GoalDep, LLMDep, SessionDep, SettingsDep, UserDep
from app.db import SessionFactory
from app.enums import GoalStatus
from app.schemas.goal import (
    ClarifyRequest,
    ClarifyResponse,
    CriteriaUpdate,
    CriterionOut,
    GoalCreate,
    GoalDetail,
    GoalDraftOut,
    GoalListItem,
)
from app.schemas.task import (
    ChecklistItemOut,
    ChecklistItemUpdate,
    CompleteDayOut,
    TodayOut,
)
from app.schemas.user import SessionRequest, UserOut
from app.services import goals as goals_service
from app.services.days import (
    DayError,
    build_today,
    complete_day,
    find_goal_by_task,
    toggle_checklist_item,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


# --------------------------------------------------------------- сессия


@router.post("/session", response_model=UserOut)
async def open_session(
    payload: SessionRequest, session: SessionDep, user: UserDep
) -> UserOut:
    """Первый запрос мини-аппа. Заодно приносит часовой пояс: Telegram его
    не передаёт, а без него стрик считается по времени сервера."""
    user.tz_offset_minutes = payload.tz_offset_minutes
    await session.commit()
    return UserOut.model_validate(user)


# --------------------------------------------------------------- цели


@router.post("/goals/clarify", response_model=ClarifyResponse)
async def clarify(
    payload: ClarifyRequest,
    session: SessionDep,
    client: LLMDep,
    settings: SettingsDep,
    user: UserDep,
) -> ClarifyResponse:
    questions = await goals_service.ask_clarifying_questions(
        session,
        client,
        settings,
        user=user,
        title=payload.title,
        duration_days=payload.duration_days,
    )
    await session.commit()
    return ClarifyResponse(questions=questions)


@router.post("/goals", response_model=GoalDraftOut, status_code=status.HTTP_201_CREATED)
async def create_goal(
    payload: GoalCreate,
    session: SessionDep,
    client: LLMDep,
    settings: SettingsDep,
    user: UserDep,
) -> GoalDraftOut:
    goal = await goals_service.create_goal(
        session, client, settings, user=user, payload=payload
    )
    await session.commit()
    return GoalDraftOut(
        goal=GoalListItem.model_validate(goal),
        criteria=[CriterionOut.model_validate(c) for c in goal.criteria],
    )


@router.patch("/goals/{goal_id}/criteria", response_model=list[CriterionOut])
async def update_criteria(
    payload: CriteriaUpdate, session: SessionDep, goal: GoalDep
) -> list[CriterionOut]:
    try:
        await goals_service.replace_criteria(session, goal, payload.texts)
    except goals_service.GoalError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    await session.commit()
    return [CriterionOut.model_validate(c) for c in goal.criteria]


@router.post("/goals/{goal_id}/generate", response_model=GoalListItem)
async def generate_route(
    session: SessionDep,
    client: LLMDep,
    settings: SettingsDep,
    user: UserDep,
    goal: GoalDep,
) -> GoalListItem:
    """Сборка скелета. Синхронно: человек стоит на экране генерации
    и ждёт результата, а не уходит.

    Если не получилось — цель остаётся в draft, введённое не потеряно,
    и кнопка «попробовать ещё раз» действительно работает.
    """
    try:
        await goals_service.generate_skeleton(
            session, client, settings, user=user, goal=goal
        )
    except goals_service.GoalError as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except Exception:
        await session.rollback()
        goal.status = GoalStatus.draft
        await session.commit()
        raise

    await session.commit()
    return GoalListItem.model_validate(goal)


@router.get("/goals", response_model=list[GoalListItem])
async def list_goals(session: SessionDep, user: UserDep) -> list[GoalListItem]:
    items = await goals_service.list_goals(session, user)
    return [GoalListItem.model_validate(g) for g in items]


@router.get("/goals/{goal_id}", response_model=GoalDetail)
async def goal_detail(
    session: SessionDep, user: UserDep, goal_id: uuid.UUID
) -> GoalDetail:
    goal = await goals_service.get_goal(session, user, goal_id, full=True)
    if goal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Цель не найдена")
    return GoalDetail.model_validate(goal)


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(session: SessionDep, goal: GoalDep) -> None:
    await goals_service.delete_goal(session, goal)
    await session.commit()


# --------------------------------------------------------------- день


async def _write_next_batch(goal_id: uuid.UUID, user_id: int) -> None:
    """Фоновая догенерация.

    Своя сессия: фон запускается после ответа, к этому моменту сессия
    запроса уже закрыта. Ошибку глотаем намеренно — человек её не ждёт,
    у него есть открытые дни, а попытка повторится при следующем заходе.
    """
    from app.ai import get_llm_client
    from app.config import get_settings
    from app.models import Goal, User

    settings = get_settings()
    async with SessionFactory() as session:
        try:
            user = await session.get(User, user_id)
            goal = await goals_service.get_goal(session, user, goal_id) if user else None
            if goal is None:
                return
            added = await goals_service.ensure_days(
                session, get_llm_client(), settings, user=user, goal=goal
            )
            if added:
                await session.commit()
        except Exception:
            await session.rollback()
            logger.warning("Батч для цели %s не дописался", goal_id, exc_info=True)


@router.get("/goals/{goal_id}/today", response_model=TodayOut)
async def today(
    session: SessionDep, user: UserDep, goal: GoalDep, background: BackgroundTasks
) -> TodayOut:
    """Проверка «нужен ли батч» висит здесь, а не только на завершении дня:
    так недописанный батч сам чинится при следующем заходе."""
    result = await build_today(session, user, goal)
    background.add_task(_write_next_batch, goal.id, user.id)
    return result


@router.post("/tasks/{task_id}/complete", response_model=CompleteDayOut)
async def complete(
    task_id: uuid.UUID,
    session: SessionDep,
    settings: SettingsDep,
    user: UserDep,
    background: BackgroundTasks,
) -> CompleteDayOut:
    found = await find_goal_by_task(session, user, task_id)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Задача не найдена")
    goal, task = found

    try:
        result = await complete_day(
            session, settings, user=user, goal=goal, task=task
        )
    except DayError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    await session.commit()
    background.add_task(_write_next_batch, goal.id, user.id)
    return result


@router.patch("/checklist/{item_id}", response_model=ChecklistItemOut)
async def update_checklist_item(
    item_id: uuid.UUID,
    payload: ChecklistItemUpdate,
    session: SessionDep,
    user: UserDep,
) -> ChecklistItemOut:
    try:
        item = await toggle_checklist_item(session, user, item_id, payload.is_done)
    except DayError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    await session.commit()
    return ChecklistItemOut.model_validate(item)
