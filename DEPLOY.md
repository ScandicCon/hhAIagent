# Деплой HH AI Agent

## Быстрый старт (Docker на VPS)

### 1. Сервер

Подойдёт любой VPS (Timeweb, Hetzner, Selectel): **1 CPU, 1 GB RAM**, Ubuntu 22.04+.

### 2. Установка Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

Перелогинься в SSH.

### 3. Клонирование проекта

```bash
git clone <your-repo-url> hh-ai
cd hh-ai
cp .env.example .env
nano .env   # заполни BOT_TOKEN, OPENROUTER_API_KEY, ADMIN_*
```

### 4. Запуск

```bash
docker compose up -d --build
docker compose logs -f
```

Проверка:

- API: `http://IP_СЕРВЕРА:9090/health`
- Лендинг: `http://IP_СЕРВЕРА:9090/welcome`

### 5. Домен и HTTPS (рекомендуется)

Установи Caddy или Nginx:

- `api.твой-домен.ru` → `localhost:9090`
- В `.env` обнови `BACKEND_URL=https://api.твой-домен.ru` (для бота не нужен с Docker — он ходит на `http://api:8000`)

### 6. Обновление

```bash
git pull
docker compose up -d --build
```

---

## Локально (Windows)

```powershell
.\run_backend.ps1
.\run_bot.ps1
```

---

## Переменные для продакшена

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен от @BotFather |
| `OPENROUTER_API_KEY` | Ключ OpenRouter |
| `ADMIN_TELEGRAM_IDS` | Твой Telegram ID |
| `ADMIN_API_KEY` | Секрет для API |
| `PROMO_CODES` | `LAUNCH2026:pro,FRIEND:pro` |
| `PRO_CONTACT` | @username для оплаты |
| `PRO_PRICE_RUB` | Цена в рублях |

---

## Бэкап БД

```bash
docker compose exec api cp /app/data/hh_agent.db /app/data/backup-$(date +%F).db
docker cp hh-ai-api-1:/app/data/backup-*.db ./
```

---

## Мониторинг

```bash
docker compose ps
docker compose logs api --tail 50
docker compose logs bot --tail 50
```
