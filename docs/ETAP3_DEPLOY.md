# Этап 3: выкладка в прод (Timeweb)

Краткий чеклист после локальной проверки бота.

## 1. Подготовка

- [ ] Код на GitHub (без `.env`)
- [ ] Домен (например `api.твой-сайт.ru`)
- [ ] Аккаунт [Timeweb Cloud](https://timeweb.cloud) — VPS Ubuntu 22.04, 1 CPU / 1–2 GB RAM

## 2. Сервер

```bash
ssh root@IP_СЕРВЕРА
curl -fsSL https://get.docker.com | sh
git clone <repo> /opt/hh-ai && cd /opt/hh-ai
cp .env.example .env
nano .env
```

Минимум в `.env` на сервере:

```env
BOT_TOKEN=
OPENROUTER_API_KEY=
ADMIN_TELEGRAM_IDS=
ADMIN_API_KEY=длинная-случайная-строка
BOT_USERNAME=имя_бота_без_@
HH_CLIENT_ID=
HH_CLIENT_SECRET=
PUBLIC_URL=https://api.твой-домен.ru
POSTGRES_PASSWORD=длинный-случайный-пароль
PRO_PRICE_RUB=490
PROMO_CODES=LAUNCH2026:pro
```

`TELEGRAM_PROXY` на VPS обычно **не нужен** — оставь пустым.

**PostgreSQL** поднимается автоматически (`docker compose` → сервис `db`). SQLite только для лёгкого локального теста: `docker compose -f docker-compose.sqlite.yml up -d`.

```bash
docker compose up -d --build
docker compose ps
curl -s http://127.0.0.1:9090/health
```

## 3. HTTPS (Caddy)

```
api.твой-домен.ru {
    reverse_proxy localhost:9090
}
```

Проверка: `https://api.твой-домен.ru/health` → `{"status":"ok"}`

## 4. ЮKassa (авто Pro)

1. [yookassa.ru](https://yookassa.ru) → Shop ID + Secret Key  
2. В `.env`: `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY`  
3. Webhook в кабинете:

```
https://api.твой-домен.ru/payments/yookassa/webhook
```

4. В боте: «Купить Pro» → ссылка на оплату → после оплаты Pro активируется сам

## 5. Проверка в Telegram

| Шаг | Ожидание |
|-----|----------|
| `/start` + резюме | профиль создан |
| Поиск + фильтры | вакансии с городом/зарплатой |
| `/plan` | лимиты Free/Pro |
| `/invite` | реферальная ссылка |
| Дайджест вкл | утром в 9:00 МСК по последнему поиску |

## 6. Лендинг для рекламы

`https://api.твой-домен.ru/welcome` — ссылка в постах и каналах.

Подробнее: `docs/DEPLOY_TIMEWEB.md`, `MARKETING.md`.
