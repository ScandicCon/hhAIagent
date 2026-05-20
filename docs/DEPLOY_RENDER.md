# Деплой на Render.com

## Важно

- **API** — Web Service (порт 8000)
- **Бот** — Background Worker (polling 24/7)
- **БД** — PostgreSQL (SQLite на Render не сохраняется между деплоями)

## Вариант A: Blueprint (рекомендуется)

1. Залей проект на GitHub (приватный репозиторий — ок).
2. [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**.
3. Подключи репозиторий — Render прочитает `render.yaml`.
4. Заполни секреты при деплое:
   - `BOT_TOKEN`
   - `OPENROUTER_API_KEY`
   - `ADMIN_TELEGRAM_IDS`
   - `YOOKASSA_*`
   - `BOT_USERNAME`
5. После деплоя скопируй URL API, например `https://hh-ai-api.onrender.com`.
6. В **API** и **Worker** добавь (обязательно с `https://`):
   ```
   PUBLIC_URL=https://hh-ai-api.onrender.com
   BACKEND_URL=https://hh-ai-api.onrender.com
   ```
7. Перезапусти оба сервиса.

## Webhook ЮKassa

```
https://hh-ai-api.onrender.com/payments/yookassa/webhook
```

## Вариант B: Вручную

### Web Service (API)

- Docker → `Dockerfile`
- Health check: `/health`
- Env: см. `.env.example`

`DATABASE_URL` — Internal Database URL от Render Postgres.

### Background Worker (Bot)

- Docker → `Dockerfile.bot`
- `BACKEND_URL=https://hh-ai-api.onrender.com` (твой URL API)

## Лендинг

`https://hh-ai-api.onrender.com/welcome`

## Ограничения Free tier

- Сервис «засыпает» — для бота нужен **платный** Worker.
- Для продакшена: Starter plan (~$7/мес за сервис).

## Timeweb vs Render

| | Timeweb VPS | Render |
|---|-------------|--------|
| Цена | ~300₽/мес | ~$14/мес (API+Worker) |
| Контроль | Полный | Проще CI/CD |
| Бот 24/7 | Да | Нужен paid worker |

Для РФ-аудитории часто удобнее **Timeweb**.
