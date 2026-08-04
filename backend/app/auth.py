"""Проверка initData из Telegram.

Подпись Telegram и есть авторизация: ни сессий, ни JWT, ни рефреш-токенов.
Каждый запрос приносит initData, мы пересчитываем HMAC и сверяем.

Схема подписи (документация Telegram Mini Apps):
    secret     = HMAC_SHA256(key="WebAppData", message=bot_token)
    ожидаемый  = HMAC_SHA256(key=secret, message=data_check_string)
где data_check_string — все поля кроме hash, отсортированные по имени,
склеенные через перевод строки как "ключ=значение".
"""

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl


class InitDataError(Exception):
    """initData отсутствует, испорчен, протух или подписан не тем ботом."""


@dataclass(slots=True, frozen=True)
class TelegramUser:
    id: int
    username: str | None
    first_name: str | None


def validate_init_data(
    init_data: str, bot_token: str, *, ttl_seconds: int
) -> TelegramUser:
    if not init_data:
        raise InitDataError("initData не передан")

    try:
        # strict_parsing ловит мусор вместо query-строки.
        fields = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError as exc:
        raise InitDataError("initData не разбирается") from exc

    received_hash = fields.pop("hash", None)
    if not received_hash:
        raise InitDataError("В initData нет hash")

    data_check_string = "\n".join(
        f"{key}={fields[key]}" for key in sorted(fields)
    )
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(
        secret, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    # compare_digest, а не ==: обычное сравнение строк утекает время
    # и позволяет подбирать подпись побайтово.
    if not hmac.compare_digest(expected, received_hash):
        raise InitDataError("Подпись не сходится")

    auth_date = fields.get("auth_date")
    if not auth_date or not auth_date.isdigit():
        raise InitDataError("В initData нет auth_date")
    if time.time() - int(auth_date) > ttl_seconds:
        raise InitDataError("initData протух")

    raw_user = fields.get("user")
    if not raw_user:
        raise InitDataError("В initData нет пользователя")
    try:
        user = json.loads(raw_user)
        user_id = int(user["id"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise InitDataError("Пользователь в initData испорчен") from exc

    return TelegramUser(
        id=user_id,
        username=user.get("username"),
        first_name=user.get("first_name"),
    )


def sign_init_data(payload: dict[str, str], bot_token: str) -> str:
    """Подписать initData — нужно только тестам и локальной отладке.

    Держим рядом с проверкой намеренно: если поменяется схема подписи,
    обе стороны поедут вместе и тест это поймает.
    """
    data_check_string = "\n".join(f"{k}={payload[k]}" for k in sorted(payload))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    signature = hmac.new(
        secret, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    parts = [f"{k}={v}" for k, v in payload.items()]
    parts.append(f"hash={signature}")
    from urllib.parse import quote

    return "&".join(
        f"{p.split('=', 1)[0]}={quote(p.split('=', 1)[1], safe='')}" for p in parts
    )
