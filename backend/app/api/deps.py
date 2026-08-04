"""Зависимости роутеров: настройки, клиент модели, текущий пользователь, цель."""

import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import get_llm_client
from app.ai.client import LLMClient
from app.auth import InitDataError, validate_init_data
from app.config import Settings, get_settings
from app.db import get_session
from app.models import Goal, User
from app.services.goals import get_goal

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]
LLMDep = Annotated[LLMClient, Depends(get_llm_client)]


async def current_user(
    session: SessionDep,
    settings: SettingsDep,
    x_telegram_init_data: Annotated[str | None, Header()] = None,
) -> User:
    """Проверяет подпись и заводит пользователя при первом заходе.

    Единственный случай, когда мини-апп не работает вовсе, — испорченный
    или чужой initData. Ошибку отдаём прямо, чтобы фронт показал
    «открой приложение через Telegram», а не крутил спиннер.
    """
    try:
        telegram_user = validate_init_data(
            x_telegram_init_data or "",
            settings.bot_token,
            ttl_seconds=settings.init_data_ttl_seconds,
        )
    except InitDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    user = await session.scalar(select(User).where(User.id == telegram_user.id))
    if user is None:
        user = User(
            id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
        )
        session.add(user)
        await session.flush()
    elif user.username != telegram_user.username:
        # Человек сменил ник — обновляем, чтобы в базе не было мусора.
        user.username = telegram_user.username

    return user


UserDep = Annotated[User, Depends(current_user)]


async def owned_goal(
    session: SessionDep,
    user: UserDep,
    goal_id: Annotated[uuid.UUID, Path()],
) -> Goal:
    """Цель текущего пользователя или 404.

    Именно 404, а не 403: чужой id не должен подтверждать, что такая
    цель вообще существует.
    """
    goal = await get_goal(session, user, goal_id)
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Цель не найдена"
        )
    return goal


GoalDep = Annotated[Goal, Depends(owned_goal)]
