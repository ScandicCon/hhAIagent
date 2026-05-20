# Пошаговый деплой на Timeweb (с нуля)

Делай шаги по порядку. После каждого блока — проверка «✓».

---

## Шаг 0. На своём ПК (Windows)

### 0.1. Залей код на GitHub (если ещё нет)

```powershell
cd C:\Users\Даниил\Desktop\hh.ai
git init
git add .
git commit -m "deploy"
```

Создай репозиторий на GitHub (приватный можно). **Не коммить `.env`** — он в `.gitignore`.

```powershell
git remote add origin https://github.com/ТВОЙ_ЛОГИН/hh-ai.git
git push -u origin main
```

Без GitHub: архивируй папку (без `.env` и `venv`) и залей на сервер через WinSCP в `/opt/hh-ai`.

### 0.2. Подготовь значения для `.env` на сервере

| Переменная | Где взять |
|------------|-----------|
| `BOT_TOKEN` | @BotFather |
| `OPENROUTER_API_KEY` | openrouter.ai |
| `ADMIN_TELEGRAM_IDS` | @userinfobot → твой id |
| `ADMIN_API_KEY` | любая длинная случайная строка |
| `BOT_USERNAME` | имя бота без @, например `HHSearchVacanciesBot` |
| `HH_CLIENT_ID` / `HH_CLIENT_SECRET` | dev.hh.ru |
| `POSTGRES_PASSWORD` | придумай сильный пароль |
| `PUBLIC_URL` | после домена: `https://api.твой-домен.ru` |

Скопируй локальный `.env` в блокнот — на сервере вставишь и поправишь.

---

## Шаг 1. VPS в Timeweb

1. [timeweb.cloud](https://timeweb.cloud) → **Облачные серверы** → создать.
2. **Ubuntu 22.04**, 1 CPU, 1–2 GB RAM.
3. Запиши **IP** и пароль root.
4. Сеть / firewall: открыты **22, 80, 443** (SSH и HTTPS).

---

## Шаг 2. Подключение по SSH

**Windows (PowerShell):**

```powershell
ssh root@IP_СЕРВЕРА
```

Первый раз спросит fingerprint — `yes`.

---

## Шаг 3. Docker и проект на сервере

```bash
curl -fsSL https://get.docker.com | sh
apt update && apt install -y git nano

mkdir -p /opt/hh-ai
cd /opt/hh-ai
```

**Вариант A — Git:**

```bash
git clone https://github.com/ТВОЙ_ЛОГИН/hh-ai.git .
```

**Вариант B — уже залил файлы через WinSCP** — просто `cd /opt/hh-ai`.

```bash
cp .env.example .env
nano .env
```

Вставь секреты. **Обязательно на сервере:**

```env
POSTGRES_PASSWORD=очень-длинный-пароль-123
TELEGRAM_PROXY=
PUBLIC_URL=https://api.ТВОЙ-ДОМЕН.ru
BOT_USERNAME=HHSearchVacanciesBot
ADMIN_TELEGRAM_IDS=961429941
ADMIN_API_KEY=...
BOT_TOKEN=...
OPENROUTER_API_KEY=...
HH_CLIENT_ID=...
HH_CLIENT_SECRET=...
PRO_PRICE_RUB=490
PROMO_CODES=LAUNCH2026:pro
```

Сохрани: `Ctrl+O`, Enter, `Ctrl+X`.

---

## Шаг 4. Запуск контейнеров

```bash
cd /opt/hh-ai
docker compose up -d --build
```

Подожди 2–5 минут (первая сборка). Проверка:

```bash
docker compose ps
```

Все три сервиса (`db`, `api`, `bot`) — **running** / **healthy**.

```bash
curl -s http://127.0.0.1:9090/health
```

Ожидается: `{"status":"ok"}` или похожий JSON.

Логи при ошибке:

```bash
docker compose logs api --tail 50
docker compose logs bot --tail 50
docker compose logs db --tail 20
```

---

## Шаг 5. Домен и HTTPS

### 5.1. DNS

В панели домена (Timeweb / reg.ru и т.д.):

- тип **A**
- имя `api` (или как хочешь)
- значение **IP VPS**

Через 5–30 минут: `ping api.твой-домен.ru` → IP сервера.

### 5.2. Caddy (авто HTTPS)

На сервере:

```bash
apt install -y caddy
nano /etc/caddy/Caddyfile
```

Содержимое (замени домен):

```
api.твой-домен.ru {
    reverse_proxy localhost:9090
}
```

```bash
systemctl enable caddy
systemctl reload caddy
```

Проверка в браузере:

`https://api.твой-домен.ru/health`

### 5.3. Обнови `.env`

```bash
nano /opt/hh-ai/.env
```

Убедись: `PUBLIC_URL=https://api.твой-домен.ru`

```bash
cd /opt/hh-ai
docker compose restart api bot
```

Лендинг: `https://api.твой-домен.ru/welcome`

---

## Шаг 6. Проверка бота в Telegram

1. Открой бота → `/start` → резюме текстом.
2. **Искать вакансии** → запрос → фильтры → **Искать**.
3. `/plan` — лимиты.
4. `/invite` — реферальная ссылка.

Если бот молчит:

```bash
docker compose logs bot -f
```

На VPS **не нужен** `TELEGRAM_PROXY` — строка пустая.

---

## Шаг 7. ЮKassa (можно позже)

1. [yookassa.ru](https://yookassa.ru) → магазин → Shop ID + Secret.
2. В `.env` на сервере:

```env
YOOKASSA_SHOP_ID=...
YOOKASSA_SECRET_KEY=...
```

3. Webhook в кабинете ЮKassa:

```
https://api.твой-домен.ru/payments/yookassa/webhook
```

4. `docker compose restart api`

В боте **«Купить Pro»** должна открываться ссылка на оплату.

---

## Шаг 8. Обновление после правок в коде

На ПК: `git push`

На сервере:

```bash
cd /opt/hh-ai
git pull
docker compose up -d --build
```

---

## Бэкап PostgreSQL

```bash
docker compose exec db pg_dump -U hh hh_agent > backup_$(date +%F).sql
```

---

## Частые проблемы

| Симптом | Решение |
|---------|---------|
| `api` не healthy | `docker compose logs api` — часто нет ключа OpenRouter |
| `bot` падает | проверь `BOT_TOKEN`, пустой `TELEGRAM_PROXY` |
| 502 с домена | Caddy смотрит на `9090`, `curl localhost:9090/health` |
| Пустая БД после деплоя | нормально — снова `/start` и резюме |
| Нет интернета у контейнера | firewall Timeweb, DNS |

---

Когда дойдёшь до шага — напиши номер шага и что видишь (ошибка или скрин текста), разберём точечно.
