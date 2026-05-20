# Деплой на Timeweb Cloud (VPS)

## 1. Создай VPS

- Ubuntu 22.04
- 1 CPU, 1–2 GB RAM
- Открой порты: **22, 80, 443** (9090 только для теста)

## 2. Подключись по SSH

```bash
ssh root@IP_СЕРВЕРА
```

## 3. Установи Docker

```bash
curl -fsSL https://get.docker.com | sh
apt install -y git
```

## 4. Загрузи проект

```bash
git clone <repo> /opt/hh-ai
cd /opt/hh-ai
cp .env.example .env
nano .env
```

Заполни минимум:

```env
BOT_TOKEN=
OPENROUTER_API_KEY=
ADMIN_TELEGRAM_IDS=
ADMIN_API_KEY=случайная-строка
PUBLIC_URL=https://api.твой-домен.ru
BOT_USERNAME=HHSearchVacanciesBot

# PostgreSQL (обязательно смени пароль на сервере)
POSTGRES_PASSWORD=длинный-случайный-пароль
# DATABASE_URL можно не указывать — подставится из docker-compose

YOOKASSA_SHOP_ID=
YOOKASSA_SECRET_KEY=
PRO_PRICE_RUB=490
```

**База:** в `docker compose` по умолчанию **PostgreSQL** (сервис `db`). Данные в volume `pg_data` — не теряются при перезапуске контейнеров.

## 5. Запуск

```bash
docker compose up -d --build
docker compose logs -f
```

## 6. Домен + HTTPS (Caddy)

```bash
apt install -y caddy
nano /etc/caddy/Caddyfile
```

```
api.твой-домен.ru {
    reverse_proxy localhost:9090
}
```

```bash
systemctl reload caddy
```

В `.env` обнови `PUBLIC_URL=https://api.твой-домен.ru`.

## 7. Webhook ЮKassa

В кабинете ЮKassa укажи URL:

```
https://api.твой-домен.ru/payments/yookassa/webhook
```

## 8. Автозапуск

Docker с `restart: unless-stopped` уже настроен в `docker-compose.yml`.

## Полезные команды

```bash
docker compose ps
docker compose restart bot
docker compose logs api --tail 100
```
