"""Четыре механики.

Каждая — тонкая обёртка: собрать пользовательское сообщение, назвать схему,
отдать в generate_structured. Ни базы, ни FastAPI, ни глобального состояния —
поэтому всё это тестируется на фейковом клиенте без ключа и без сети.

Температуры подобраны по задаче: где нужен разбор факта — низкая,
где нужен внятный план — повыше.
"""

from app.ai import prompts
from app.ai.client import LLMClient
from app.ai.structured import Structured, generate_structured
from app.config import Settings
from app.schemas.ai import (
    AIClarifyResult,
    AICriteriaResult,
    AIDayBatch,
    AIRouteSkeleton,
    AISimplifiedTask,
)

Answers = list[tuple[str, str]]

TEMP_CLARIFY = 0.2
TEMP_CRITERIA = 0.3
TEMP_ROUTE = 0.7
TEMP_SIMPLIFY = 0.5


async def clarify_goal(
    client: LLMClient, settings: Settings, *, title: str, duration_days: int
) -> Structured[AIClarifyResult]:
    """Нужны ли уточняющие вопросы. Пустой список — шаг пропускается."""
    return await generate_structured(
        client,
        AIClarifyResult,
        system=prompts.SYSTEM_CLARIFY,
        user=prompts.build_clarify_user(title, duration_days),
        max_tokens=settings.max_tokens_clarify,
        temperature=TEMP_CLARIFY,
    )


async def make_criteria(
    client: LLMClient,
    settings: Settings,
    *,
    title: str,
    duration_days: int,
    answers: Answers,
) -> Structured[AICriteriaResult]:
    """Три-четыре критерия готовности и категория для карточки."""
    return await generate_structured(
        client,
        AICriteriaResult,
        system=prompts.SYSTEM_CRITERIA,
        user=prompts.build_criteria_user(title, duration_days, answers),
        max_tokens=settings.max_tokens_criteria,
        temperature=TEMP_CRITERIA,
    )


async def make_skeleton(
    client: LLMClient,
    settings: Settings,
    *,
    title: str,
    duration_days: int,
    criteria: list[str],
    answers: Answers,
) -> Structured[AIRouteSkeleton]:
    """Фазы на весь срок плюс первая неделя дней.

    Всё, что дальше первой недели, пишется батчами: длинная генерация
    и медленная, и рвётся по потолку токенов, и к концу теряет качество.
    """
    return await generate_structured(
        client,
        AIRouteSkeleton,
        system=prompts.SYSTEM_SKELETON,
        user=prompts.build_skeleton_user(
            title, duration_days, criteria, answers, settings.batch_size_days
        ),
        max_tokens=settings.max_tokens_skeleton,
        temperature=TEMP_ROUTE,
    )


async def make_batch(
    client: LLMClient,
    settings: Settings,
    *,
    title: str,
    duration_days: int,
    criteria: list[str],
    current_phase: str,
    written_titles: list[str],
    recent_results: list[tuple[int, str]],
    first_day: int,
    last_day: int,
) -> Structured[AIDayBatch]:
    """Следующие дни. written_titles — только заголовки: полные описания
    раздули бы вход втрое, а для «не повторяйся» их достаточно."""
    return await generate_structured(
        client,
        AIDayBatch,
        system=prompts.SYSTEM_BATCH,
        user=prompts.build_batch_user(
            title,
            duration_days,
            criteria,
            current_phase,
            written_titles,
            recent_results,
            first_day,
            last_day,
        ),
        max_tokens=settings.max_tokens_batch,
        temperature=TEMP_ROUTE,
    )


async def simplify_task(
    client: LLMClient,
    settings: Settings,
    *,
    goal_title: str,
    day_number: int,
    task_title: str,
    task_description: str,
) -> Structured[AISimplifiedTask]:
    """Та же задача в телефонном формате. В первый срез не входит,
    но контракт и промпт готовы — включается одной строкой в роутере."""
    return await generate_structured(
        client,
        AISimplifiedTask,
        system=prompts.SYSTEM_SIMPLIFY,
        user=prompts.build_simplify_user(
            task_title, task_description, goal_title, day_number
        ),
        max_tokens=settings.max_tokens_criteria,
        temperature=TEMP_SIMPLIFY,
    )
