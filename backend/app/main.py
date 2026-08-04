"""Точка входа.

Собирает приложение, вешает CORS и превращает ошибки слоя ИИ в честные
ответы: человек должен видеть «не получилось, попробуй ещё раз»,
а не бесконечный спиннер.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.ai.errors import AIInvalidResponse, AITransportError
from app.api.routes import router
from app.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="Маршрут",
    description="Большая цель превращается в маршрут из ежедневных задач",
    version="0.1.0",
)

# Мини-апп живёт на Vercel, бэкенд — отдельно. Telegram открывает
# страницу в своём вебвью, поэтому источник надо разрешить явно.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:\d+",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.exception_handler(AITransportError)
async def transport_error_handler(_: Request, exc: AITransportError) -> JSONResponse:
    logger.warning("Модель недоступна: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"detail": "Модель сейчас не отвечает. Попробуй ещё раз через минуту."},
    )


@app.exception_handler(AIInvalidResponse)
async def invalid_response_handler(_: Request, exc: AIInvalidResponse) -> JSONResponse:
    logger.warning("Модель дважды ответила не по контракту: %s", exc.reason)
    return JSONResponse(
        status_code=502,
        content={"detail": "Не получилось собрать маршрут. Попробуй ещё раз."},
    )


@app.get("/health")
async def health() -> dict[str, object]:
    """Пинг для бесплатного тарифа: инстанс засыпает через час простоя,
    и внешний крон раз в сорок минут держит его тёплым."""
    return {"ok": True, "llm": "deepseek" if settings.use_real_llm else "stub"}
