"""Настройки приложения. Всё приходит из окружения, ничего не хардкодим."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- база ---
    database_url: str = Field(
        description="postgresql+asyncpg://user:pass@host:5432/db",
    )
    db_echo: bool = False

    # --- Telegram ---
    bot_token: str = Field(description="Токен бота: им подписан initData")
    init_data_ttl_seconds: int = 60 * 60 * 24  # подпись старше суток не принимаем

    # --- DeepSeek ---
    # Пустой ключ — не ошибка: приложение поднимается на заглушке
    # и проходится целиком. Ключ вставляется, когда понадобится живая модель.
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_timeout_seconds: float = 90.0

    # Потолки вывода. Модель, которую попросили семь дней,
    # иногда решает написать тридцать — этого не должно случаться за наш счёт.
    max_tokens_clarify: int = 700
    max_tokens_criteria: int = 700
    max_tokens_skeleton: int = 4000
    max_tokens_batch: int = 3000

    # --- продуктовые правила ---
    allowed_durations: tuple[int, ...] = (30, 60, 90)
    batch_size_days: int = 7
    generate_ahead_threshold: int = 4  # дописываем, когда до края маршрута меньше
    xp_per_day: int = 50

    @property
    def use_real_llm(self) -> bool:
        return bool(self.deepseek_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    """Настройки читаются один раз за процесс."""
    return Settings()  # type: ignore[call-arg]
