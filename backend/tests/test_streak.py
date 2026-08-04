"""Стрик на границе суток — место, где легче всего ошибиться."""

from datetime import date, datetime, timedelta, timezone

from app.services.streak import local_today, next_streak

TODAY = date(2026, 8, 4)


def test_first_completion_starts_streak():
    assert next_streak(None, 0, TODAY) == 1


def test_consecutive_day_increments():
    assert next_streak(TODAY - timedelta(days=1), 11, TODAY) == 12


def test_same_day_does_not_double_count():
    """Закрыл два дня маршрута за одни сутки — стрик всё равно один."""
    assert next_streak(TODAY, 12, TODAY) == 12


def test_gap_resets_to_one():
    assert next_streak(TODAY - timedelta(days=2), 30, TODAY) == 1


def test_long_gap_resets_to_one():
    assert next_streak(date(2026, 1, 1), 99, TODAY) == 1


def test_local_date_uses_user_offset():
    """23:30 UTC — это уже завтра в Новосибирске (UTC+7).

    Считать стрик по серверной дате значит обнулять его людям посреди дня.
    """
    moment = datetime(2026, 8, 4, 23, 30, tzinfo=timezone.utc)
    assert local_today(0, now=moment) == date(2026, 8, 4)
    assert local_today(7 * 60, now=moment) == date(2026, 8, 5)


def test_local_date_handles_negative_offset():
    moment = datetime(2026, 8, 4, 2, 0, tzinfo=timezone.utc)
    assert local_today(-5 * 60, now=moment) == date(2026, 8, 3)
