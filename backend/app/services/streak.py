"""Стрик — чистая арифметика над датами.

Вынесен отдельно и без базы намеренно: это единственное место в проекте,
где легко ошибиться на границе суток, и его надо было сделать тестируемым
без единого запроса.

Правило простое. Стрик считает календарные дни, в которые человек закрыл
хотя бы один день маршрута. Пропустил сутки — обнулился. На сам маршрут
это не влияет: дни ждут человека столько, сколько нужно.
"""

from datetime import date, datetime, timedelta, timezone


def local_today(tz_offset_minutes: int, *, now: datetime | None = None) -> date:
    """Какое сегодня число у человека, а не у сервера.

    Сервер живёт в UTC, человек — в Новосибирске или где угодно ещё.
    Считать стрик по серверной дате значит обнулять его людям посреди дня.
    """
    moment = now or datetime.now(timezone.utc)
    return (moment + timedelta(minutes=tz_offset_minutes)).date()


def next_streak(
    last_completed: date | None, current_streak: int, today: date
) -> int:
    if last_completed is None:
        return 1
    if last_completed == today:
        # Второй день маршрута за одни сутки стрик не удваивает.
        return max(current_streak, 1)
    if last_completed == today - timedelta(days=1):
        return current_streak + 1
    return 1
