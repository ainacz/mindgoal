"""Эндпоинты. Роутеры тонкие: разобрать вход, позвать сервис, вернуть схему.

Про DeepSeek здесь не знает никто — только про сервисы.
"""

import logging
import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import GoalDep, LLMDep, SessionDep, SettingsDep, UserDep
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
    GenerateRequest,
)
from app.schemas.task import (
    ChecklistItemOut,
    ChecklistItemUpdate,
    CompleteDayOut,
    CompleteDayRequest,
    DailyTaskOut,
    TodayOut,
)
from app.schemas.user import SessionRequest, UserOut
from app.services import goals as goals_service
from app.services.days import (
    DayError,
    build_today,
    complete_day,
    find_goal_by_task,
    simplify_day,
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
    goal, reality_note = await goals_service.create_goal(
        session, client, settings, user=user, payload=payload
    )
    await session.commit()
    return GoalDraftOut(
        goal=GoalListItem.model_validate(goal),
        criteria=[CriterionOut.model_validate(c) for c in goal.criteria],
        reality_note=reality_note,
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
    payload: GenerateRequest,
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
            session, client, settings, user=user, goal=goal, answers=payload.answers
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


@router.get("/goals/{goal_id}/today", response_model=TodayOut)
async def today(
    session: SessionDep,
    client: LLMDep,
    settings: SettingsDep,
    user: UserDep,
    goal: GoalDep,
) -> TodayOut:
    """Экран «Сегодня».

    Если человек упёрся в край написанного маршрута — дописываем прямо
    здесь и отдаём готовый день. Фоновой задачи нет намеренно: на
    serverless её убивают сразу после ответа, и батч не дописался бы
    никогда. Ждать приходится раз в неделю и секунд десять.
    """
    result = await build_today(session, user, goal, settings.generate_ahead_threshold)
    if result.task is not None:
        return result

    added = await goals_service.ensure_days(
        session, client, settings, user=user, goal=goal
    )
    if not added:
        return result

    await session.commit()
    return await build_today(session, user, goal, settings.generate_ahead_threshold)


@router.post("/goals/{goal_id}/ensure-days", response_model=dict[str, int])
async def ensure_days(
    session: SessionDep,
    client: LLMDep,
    settings: SettingsDep,
    user: UserDep,
    goal: GoalDep,
) -> dict[str, int]:
    """Дописать батч заранее. Дёргает фронт фоном, когда до края маршрута
    осталось меньше порога, и ответа не ждёт.

    Без этого дни писались только в момент, когда человек в них упёрся:
    порог generate_ahead_threshold существовал, но вызывать ensure_days
    было некому — и раз в неделю человек стоял минуту перед пустым экраном.
    """
    added = await goals_service.ensure_days(
        session, client, settings, user=user, goal=goal
    )
    await session.commit()
    return {"added": added}


@router.post("/tasks/{task_id}/complete", response_model=CompleteDayOut)
async def complete(
    task_id: uuid.UUID,
    payload: CompleteDayRequest,
    session: SessionDep,
    settings: SettingsDep,
    user: UserDep,
) -> CompleteDayOut:
    found = await find_goal_by_task(session, user, task_id)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Задача не найдена")
    goal, task = found

    try:
        result = await complete_day(
            session,
            settings,
            user=user,
            goal=goal,
            task=task,
            result_note=payload.result_note,
        )
    except DayError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    await session.commit()
    return result


@router.post("/tasks/{task_id}/simplify", response_model=DailyTaskOut)
async def simplify(
    task_id: uuid.UUID,
    session: SessionDep,
    client: LLMDep,
    settings: SettingsDep,
    user: UserDep,
) -> DailyTaskOut:
    """«Мало времени». Синхронно, как и вся генерация: человек ждёт
    на экране, а фоновые задачи на serverless умирают вместе с ответом."""
    found = await find_goal_by_task(session, user, task_id)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Задача не найдена")
    goal, task = found

    try:
        task = await simplify_day(
            session, client, settings, user=user, goal=goal, task=task
        )
    except DayError as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    await session.commit()
    return DailyTaskOut.model_validate(task)


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
