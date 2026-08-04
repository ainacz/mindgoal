"""Проверка подписи initData. Ни базы, ни сети — чистая криптография."""

import json
import time

import pytest

from app.auth import InitDataError, TelegramUser, sign_init_data, validate_init_data

TOKEN = "123456:AAH-test-bot-token"


def make(**overrides) -> str:
    payload = {
        "auth_date": str(int(time.time())),
        "query_id": "AAH1234",
        "user": json.dumps(
            {"id": 777, "username": "dolaan", "first_name": "Долаан"},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }
    payload.update(overrides)
    return sign_init_data(payload, TOKEN)


def check(init_data: str) -> TelegramUser:
    return validate_init_data(init_data, TOKEN, ttl_seconds=86400)


def test_valid_signature_passes():
    user = check(make())
    assert user.id == 777
    assert user.username == "dolaan"
    assert user.first_name == "Долаан"


def test_wrong_bot_token_rejected():
    """Подпись от чужого бота — самый вероятный способ подделки."""
    with pytest.raises(InitDataError):
        validate_init_data(make(), "999:other-token", ttl_seconds=86400)


def test_tampered_field_rejected():
    """Меняем пользователя, оставляя чужой hash."""
    original = make()
    tampered = original.replace("777", "778")
    with pytest.raises(InitDataError):
        check(tampered)


def test_expired_init_data_rejected():
    old = make(auth_date=str(int(time.time()) - 90000))
    with pytest.raises(InitDataError):
        check(old)


def test_missing_hash_rejected():
    with pytest.raises(InitDataError):
        check("auth_date=123&user=%7B%22id%22%3A1%7D")


def test_empty_init_data_rejected():
    with pytest.raises(InitDataError):
        check("")


def test_garbage_rejected():
    with pytest.raises(InitDataError):
        check("совсем не query-строка")
