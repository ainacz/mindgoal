"""Механики на фейковом клиенте: ни сети, ни ключа, ни базы."""

import asyncio

import pytest

from app.ai.errors import AIInvalidResponse, AITransportError
from app.ai.mechanics import (
    clarify_goal,
    make_batch,
    make_criteria,
    make_skeleton,
)
from app.ai.prompts import SYSTEM_BATCH, SYSTEM_CLARIFY, SYSTEM_CRITERIA, SYSTEM_SKELETON
from app.config import Settings
from tests.fakes import FakeLLMClient, transport_error


def settings() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://x/y",
        bot_token="test",
        deepseek_api_key="test",
    )


def day(n: int, minutes: int = 30) -> dict:
    return {
        "day_number": n,
        "title": f"Написать разбор {n}",
        "estimated_minutes": minutes,
        "description": "Конкретное действие, которое можно сделать сегодня.",
        "hint": None,
        "checklist": ["первый пункт", "второй пункт"],
    }


SKELETON_OK = {
    "phases": [
        {"title": "База Python и API", "start_day": 1, "end_day": 30},
        {"title": "RAG и векторные базы", "start_day": 31, "end_day": 60},
        {"title": "Агенты и деплой", "start_day": 61, "end_day": 90},
    ],
    "days": [day(1, 15), *[day(n) for n in range(2, 8)]],
}


# --------------------------------------------------------------- уточнение


def test_clarify_concrete_goal_asks_nothing():
    fake = FakeLLMClient(
        [FakeLLMClient.json_response({"needs_clarification": False, "questions": []})]
    )
    result = asyncio.run(
        clarify_goal(fake, settings(), title="Стать AI-инженером", duration_days=90)
    )
    assert result.data.questions == []
    assert result.attempts == 1
    assert fake.system_prompts == [SYSTEM_CLARIFY]


def test_clarify_vague_goal_returns_questions():
    fake = FakeLLMClient(
        [
            FakeLLMClient.json_response(
                {
                    "needs_clarification": True,
                    "questions": [
                        {"question": "Какой у тебя уровень?", "options": ["Ноль", "Средний"]},
                        {"question": "Сколько минут в день?", "options": ["15", "30", "60"]},
                    ],
                }
            )
        ]
    )
    result = asyncio.run(
        clarify_goal(fake, settings(), title="Хочу бизнес", duration_days=60)
    )
    assert len(result.data.questions) == 2


# --------------------------------------------------------------- критерии


def test_criteria_returns_measurable_list():
    fake = FakeLLMClient(
        [
            FakeLLMClient.json_response(
                {
                    "category": "Карьера",
                    "criteria": [
                        "Задеплоен сервис с публичной ссылкой",
                        "На GitHub три репозитория с README",
                        "Пройдено два технических собеседования",
                    ],
                }
            )
        ]
    )
    result = asyncio.run(
        make_criteria(
            fake,
            settings(),
            title="Стать AI-инженером",
            duration_days=90,
            answers=[("Код писал?", "Немного")],
        )
    )
    assert result.data.category == "Карьера"
    assert fake.system_prompts == [SYSTEM_CRITERIA]


# --------------------------------------------------------------- ретрай


def test_retries_once_and_succeeds():
    """Первый ответ кривой, второй нормальный — механика этого не замечает."""
    bad = FakeLLMClient.json_response(
        {"category": "Карьера", "criteria": ["Разобрался с RAG", "Ещё что-то", "И третье"]}
    )
    good = FakeLLMClient.json_response(
        {
            "category": "Карьера",
            "criteria": [
                "Задеплоен сервис с публичной ссылкой",
                "На GitHub три репозитория",
                "Пройдено два собеседования",
            ],
        }
    )
    fake = FakeLLMClient([bad, good])
    result = asyncio.run(
        make_criteria(
            fake, settings(), title="Стать AI-инженером", duration_days=90, answers=[]
        )
    )
    assert result.attempts == 2
    assert fake.call_count == 2


def test_retry_keeps_system_prompt_identical():
    """Ключевое для кэша: системное сообщение во втором заходе то же самое.

    Стоит его тронуть — префикс перестанет совпадать, и вход подорожает
    в пятьдесят раз.
    """
    bad = "не json вовсе"
    good = FakeLLMClient.json_response(
        {"needs_clarification": False, "questions": []}
    )
    fake = FakeLLMClient([bad, good])
    asyncio.run(clarify_goal(fake, settings(), title="Купить BMW", duration_days=30))

    assert fake.call_count == 2
    assert fake.system_prompts[0] == fake.system_prompts[1] == SYSTEM_CLARIFY
    # Во второй заход ушла претензия к предыдущему ответу
    assert "не прошёл проверку" in fake.calls[1][-1]["content"]


def test_gives_up_after_second_failure():
    fake = FakeLLMClient(["{}", "{}"])
    with pytest.raises(AIInvalidResponse):
        asyncio.run(
            clarify_goal(fake, settings(), title="Хочу бизнес", duration_days=30)
        )
    assert fake.call_count == 2


def test_transport_error_is_not_retried():
    """Сетевую ошибку переспрашивать бессмысленно — она не про содержание."""
    fake = FakeLLMClient([transport_error()])
    with pytest.raises(AITransportError):
        asyncio.run(
            clarify_goal(fake, settings(), title="Купить BMW", duration_days=30)
        )
    assert fake.call_count == 1


# --------------------------------------------------------------- маршрут


def test_skeleton_parsed_and_limited_to_batch_size():
    fake = FakeLLMClient([FakeLLMClient.json_response(SKELETON_OK)])
    cfg = settings()
    result = asyncio.run(
        make_skeleton(
            fake,
            cfg,
            title="Стать AI-инженером",
            duration_days=90,
            criteria=["Задеплоен сервис"],
            answers=[],
        )
    )
    assert len(result.data.days) == cfg.batch_size_days
    assert result.data.days[0].estimated_minutes <= 20
    assert len(result.data.phases) == 3
    assert fake.system_prompts == [SYSTEM_SKELETON]
    assert fake.max_tokens_seen == [cfg.max_tokens_skeleton]


def test_batch_gets_written_titles_but_not_descriptions():
    """Во вход батча уходят только заголовки — иначе контекст растёт втрое."""
    fake = FakeLLMClient(
        [FakeLLMClient.json_response({"days": [day(n) for n in range(8, 15)]})]
    )
    asyncio.run(
        make_batch(
            fake,
            settings(),
            title="Стать AI-инженером",
            duration_days=90,
            criteria=["Задеплоен сервис"],
            current_phase="База Python и API",
            written_titles=["Поставить Python", "Написать первый скрипт"],
            first_day=8,
            last_day=14,
        )
    )
    user_message = fake.calls[0][1]["content"]
    assert "Поставить Python" in user_message
    assert "Конкретное действие" not in user_message
    assert fake.system_prompts == [SYSTEM_BATCH]


def test_skeleton_with_broken_phases_is_rejected_twice():
    broken = FakeLLMClient.json_response(
        {
            "phases": [
                {"title": "База", "start_day": 1, "end_day": 30},
                {"title": "RAG", "start_day": 40, "end_day": 60},
            ],
            "days": [day(1, 15)],
        }
    )
    fake = FakeLLMClient([broken, broken])
    with pytest.raises(AIInvalidResponse) as exc:
        asyncio.run(
            make_skeleton(
                fake,
                settings(),
                title="Стать AI-инженером",
                duration_days=90,
                criteria=["Задеплоен сервис"],
                answers=[],
            )
        )
    assert "не стыкуются" in str(exc.value)


# --------------------------------------------------------------- заглушка


def test_stub_passes_the_same_contracts():
    """Заглушка обязана проходить те же схемы, что и живая модель.

    Иначе она врёт: приложение на ней работает, а с ключом ломается.
    """
    from app.ai.stub import StubLLMClient

    stub = StubLLMClient()
    cfg = settings()

    clar = asyncio.run(
        clarify_goal(stub, cfg, title="Стать AI-инженером", duration_days=90)
    )
    assert clar.data.questions == []

    vague = asyncio.run(clarify_goal(stub, cfg, title="Хочу бизнес", duration_days=60))
    assert len(vague.data.questions) == 3

    crit = asyncio.run(
        make_criteria(stub, cfg, title="Хочу бизнес", duration_days=60, answers=[])
    )
    assert len(crit.data.criteria) >= 3

    skel = asyncio.run(
        make_skeleton(
            stub,
            cfg,
            title="Хочу бизнес",
            duration_days=90,
            criteria=crit.data.criteria,
            answers=[],
        )
    )
    assert skel.data.phases[0].start_day == 1
    assert skel.data.phases[-1].end_day == 90
    assert skel.data.days[0].estimated_minutes <= 20


def test_stub_writes_any_requested_batch():
    """Маршрут должен проходиться до конца — значит заглушка обязана
    выдавать любой диапазон дней, а не только первую неделю."""
    from app.ai.stub import StubLLMClient

    batch = asyncio.run(
        make_batch(
            StubLLMClient(),
            settings(),
            title="Хочу бизнес",
            duration_days=90,
            criteria=["Опубликован результат"],
            current_phase="Практика и объём",
            written_titles=["Поставить всё нужное"],
            first_day=84,
            last_day=90,
        )
    )
    assert [d.day_number for d in batch.data.days] == list(range(84, 91))
