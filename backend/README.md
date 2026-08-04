# Бэкенд «Маршрут»

## Запуск

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                                 # заполнить BOT_TOKEN
docker compose -f docker-compose.test.yml up -d      # Postgres на 5433
alembic upgrade head
uvicorn app.main:app --reload
```

Ключ DeepSeek можно не заполнять: без него работает заглушка, маршрут
проходится целиком. Документация API — на `/docs`.

## Деплой

Vercel, отдельный проект с Root Directory = `backend`. FastAPI собирается
в одну функцию из `app/main.py`, `vercel.json` только поднимает потолок
времени до 120 секунд — генерации маршрута хватает.

Фоновых задач нет намеренно: на serverless их убивают сразу после ответа.
Недостающие дни дописываются синхронно в `/today`, когда человек упёрся
в край маршрута.

Миграции накатываются вручную с локальной машины: `alembic upgrade head`
с прод-строкой в `.env`. База одна и та же.

## Тесты

```bash
pytest
```

Ни один тест не ходит в сеть и не требует ключа: модель подменяется фейком.

## Что где

| Папка | Что внутри | Про что не знает |
|---|---|---|
| `app/models/` | таблицы SQLAlchemy | про HTTP и про ИИ |
| `app/schemas/` | контракты Pydantic | про базу |
| `app/ai/` | промпты, клиент, механики | про базу и про FastAPI |
| `app/services/` | бизнес-логика | про HTTP |
| `app/api/` | роутеры | про DeepSeek |

Правило: файл длиннее 200 строк делает две вещи и подлежит разрезанию.
