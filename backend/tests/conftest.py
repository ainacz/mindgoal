"""Общие настройки тестов.

Переменные окружения выставляем до импорта приложения: Settings читает их
на этапе конструирования, и без них падает даже тест, который в базу
не ходит.
"""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/marshrut_test")
os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("DEEPSEEK_API_KEY", "test-key")
