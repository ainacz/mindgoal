"""Живая проверка DeepSeek. Запускать руками, когда появится ключ.

    python -m scripts.smoke_ai "Стать AI-инженером" 90

Прогоняет три механики подряд и печатает расход. Второй прогон подряд
должен показать заметный cache hit — если он остался нулевым, значит
системный промпт где-то собирается из переменных.
"""

import asyncio
import sys

from app.ai.client import DeepSeekClient
from app.ai.mechanics import clarify_goal, make_criteria, make_skeleton
from app.config import get_settings
from app.services.ai_usage import estimate_cost_usd


def report(name: str, result) -> None:
    u = result.usage
    print(
        f"{name:<10} попыток={result.attempts} {result.latency_ms:>6} мс  "
        f"вход={u.prompt_tokens:>6} (в кэше {u.prompt_cache_hit_tokens:>6})  "
        f"выход={u.completion_tokens:>5}  ≈ ${estimate_cost_usd(u):.5f}"
    )


async def main(title: str, duration: int) -> None:
    settings = get_settings()
    client = DeepSeekClient(
        settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        timeout=settings.deepseek_timeout_seconds,
    )
    try:
        clar = await clarify_goal(client, settings, title=title, duration_days=duration)
        report("уточнение", clar)
        answers = [(q.question, q.options[0]) for q in clar.data.questions]
        for q in clar.data.questions:
            print(f"    ? {q.question} — {', '.join(q.options)}")

        crit = await make_criteria(
            client, settings, title=title, duration_days=duration, answers=answers
        )
        report("критерии", crit)
        for c in crit.data.criteria:
            print(f"    · {c}")

        skel = await make_skeleton(
            client,
            settings,
            title=title,
            duration_days=duration,
            criteria=crit.data.criteria,
            answers=answers,
        )
        report("скелет", skel)
        for p in skel.data.phases:
            print(f"    [{p.start_day}—{p.end_day}] {p.title}")
        for d in skel.data.days:
            print(f"    день {d.day_number:>2} · {d.estimated_minutes:>2} мин · {d.title}")

        total = sum(
            estimate_cost_usd(r.usage) for r in (clar, crit, skel)
        )
        print(f"\nитого за прогон ≈ ${total:.5f}")
    finally:
        await client.aclose()


if __name__ == "__main__":
    goal = sys.argv[1] if len(sys.argv) > 1 else "Стать AI-инженером"
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
    asyncio.run(main(goal, days))
