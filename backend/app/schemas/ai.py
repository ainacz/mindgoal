"""Контракты с моделью.

Это то, что DeepSeek обязан вернуть. Все схемы строгие: лишнее поле,
пропущенное поле или неверный тип — это провал вызова и ретрай, а не
попытка догадаться. Дешевле спросить модель ещё раз, чем разбирать потом
маршрут, в котором половина дней без описания.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import StrictModel

# --------------------------------------------------------------- уточнение


class AIClarifyQuestion(StrictModel):
    question: str = Field(min_length=5, max_length=200)
    options: list[str] = Field(min_length=2, max_length=4)


class AIClarifyResult(StrictModel):
    """Вопросы задаются всегда: без точки старта маршрут не построить.

    Раньше здесь был флаг «цель конкретная, уточнять нечего» — и на
    «пробежать марафон» мы не спрашивали ничего, а потом строили дни
    для человека, про которого не знали, бегает он сейчас или нет.
    """

    questions: list[AIClarifyQuestion] = Field(min_length=1, max_length=3)


# --------------------------------------------------------------- критерии


class AICriteriaResult(StrictModel):
    category: str = Field(min_length=2, max_length=40)
    criteria: list[str] = Field(min_length=3, max_length=4)

    # Заполняется, только когда срок не бьётся с уровнем. Не блокирует
    # создание цели: человек вправе взяться за невозможное, но должен
    # узнать об этом до, а не на тридцатый день.
    reality_note: str | None = Field(default=None, max_length=250)

    @field_validator("criteria")
    @classmethod
    def _measurable(cls, values: list[str]) -> list[str]:
        """Дешёвая страховка от формулировок состояния.

        Промпт это запрещает, но модель иногда всё равно пишет «разобрался
        с основами». Ловим самые частые случаи здесь, до записи в базу.
        """
        banned = (
            "разобрал",
            "изучил",
            "понял",
            "привычк",
            "уверенн",
            "научил",
            "освоил",
            "стало легче",
        )
        for text in values:
            low = text.lower()
            if any(word in low for word in banned):
                raise ValueError(f"Критерий не измерим: {text!r}")
        return values


# --------------------------------------------------------------- маршрут


class AIPhase(StrictModel):
    title: str = Field(min_length=3, max_length=120)
    start_day: int = Field(ge=1)
    end_day: int = Field(ge=1)

    @model_validator(mode="after")
    def _range(self) -> "AIPhase":
        if self.end_day < self.start_day:
            raise ValueError("end_day меньше start_day")
        return self


class AIDay(StrictModel):
    day_number: int = Field(ge=1)
    title: str = Field(min_length=5, max_length=200)
    estimated_minutes: int = Field(ge=5, le=240)
    description: str = Field(min_length=10, max_length=600)
    hint: str | None = Field(default=None, max_length=400)
    checklist: list[str] = Field(min_length=1, max_length=5)


class AIRouteSkeleton(StrictModel):
    """Первый вызов генерации: фазы на весь срок и первая неделя дней."""

    phases: list[AIPhase] = Field(min_length=1, max_length=6)
    days: list[AIDay] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def _phases_cover_days(self) -> "AIRouteSkeleton":
        ordered = sorted(self.phases, key=lambda p: p.start_day)
        if ordered[0].start_day != 1:
            raise ValueError("Первая фаза должна начинаться с дня 1")
        for previous, current in zip(ordered, ordered[1:]):
            if current.start_day != previous.end_day + 1:
                raise ValueError("Фазы не стыкуются: между ними дыра или нахлёст")

        numbers = [d.day_number for d in self.days]
        if numbers != list(range(1, len(numbers) + 1)):
            raise ValueError("Дни скелета должны идти подряд с первого")
        return self

    @model_validator(mode="after")
    def _first_day_is_small(self) -> "AIRouteSkeleton":
        """День 1 — физическое действие на 15 минут. Это правило продукта,
        а не пожелание: с него начинается вся привычка."""
        first = next((d for d in self.days if d.day_number == 1), None)
        if first is not None and first.estimated_minutes > 20:
            raise ValueError("Первый день длиннее 20 минут")
        return self


class AIDayBatch(StrictModel):
    """Догенерация следующих дней."""

    days: list[AIDay] = Field(min_length=1, max_length=14)

    @model_validator(mode="after")
    def _sequential(self) -> "AIDayBatch":
        numbers = [d.day_number for d in self.days]
        if numbers != sorted(numbers) or len(set(numbers)) != len(numbers):
            raise ValueError("Дни батча должны идти подряд и без повторов")
        return self


# --------------------------------------------------------------- упрощение


class AISimplifiedTask(StrictModel):
    """Та же задача в телефонном формате: без компьютера, короче."""

    title: str = Field(min_length=5, max_length=200)
    estimated_minutes: int = Field(ge=5, le=30)
    description: str = Field(min_length=10, max_length=600)
    hint: str | None = Field(default=None, max_length=400)
    checklist: list[str] = Field(min_length=1, max_length=3)


# --------------------------------------------------------------- расход


class TokenUsage(BaseModel):
    """То, что приходит в поле usage ответа DeepSeek.

    Схема нестрогая намеренно: провайдер добавляет поля в usage без
    предупреждения (детализация токенов, рассуждения), и падать из-за
    лишнего ключа в статистике — глупо.
    """

    model_config = ConfigDict(extra="ignore")

    prompt_tokens: int = 0
    completion_tokens: int = 0
    prompt_cache_hit_tokens: int = 0
    prompt_cache_miss_tokens: int = 0
    total_tokens: int = 0
