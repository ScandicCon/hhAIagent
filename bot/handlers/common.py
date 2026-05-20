import json

from aiogram.types import Message
from httpx import HTTPStatusError, RequestError

from bot.config import BACKEND_URL
from bot.utils.usage_text import upgrade_message


async def reply_backend_error(message: Message, error: Exception) -> None:
    if isinstance(error, HTTPStatusError):
        status = error.response.status_code
        detail = error.response.text.strip() or str(error)

        if status == 402:
            try:
                payload = error.response.json()
                detail_obj = payload.get("detail", payload)
                if isinstance(detail_obj, dict):
                    message_text = detail_obj.get("message", "Лимит исчерпан")
                else:
                    message_text = str(detail_obj)
            except json.JSONDecodeError:
                message_text = "Лимит исчерпан"

            await message.answer(
                f"{message_text}\n\n{upgrade_message()}",
                parse_mode="HTML",
            )
            return

        if status == 503 and "ai_rate_limit" in detail:
            await message.answer(
                "AI временно перегружен (лимит OpenRouter).\n"
                "Подожди 1–2 минуты и повтори поиск.\n\n"
                "Совет: в .env можно сменить модель:\n"
                "OPENROUTER_MODELS=openai/gpt-4o-mini,google/gemini-2.0-flash-001"
            )
            return

        if status == 502:
            try:
                payload = error.response.json()
                detail_obj = payload.get("detail", payload)
                code = detail_obj.get("code") if isinstance(detail_obj, dict) else None
                if code == "hh_timeout":
                    await message.answer(
                        "hh.ru долго не отвечает.\n"
                        "Подожди 1–2 минуты и повтори поиск.\n"
                        "Если часто так — проверь VPN или интернет."
                    )
                    return
                if code == "apply_daily_limit":
                    await message.answer(
                        "Достигнут лимит откликов на сегодня.\n"
                        "Попробуй завтра или отключи автоотклик."
                    )
                    return
                if code == "hh_resumes_forbidden":
                    msg = detail_obj.get("message", "Нет доступа к резюме на hh.ru")
                    await message.answer(msg, parse_mode="HTML", disable_web_page_preview=True)
                    return
                if code in {"hh_token_rate_limit", "hh_token"}:
                    await message.answer(
                        "Временная ошибка hh.ru (токен).\n"
                        "Подожди 1–2 минуты и повтори поиск."
                    )
                    return
            except json.JSONDecodeError:
                pass

        if status in {502, 503, 504}:
            await message.answer(
                f"Backend вернул {status} — на порту не наш API или он перезапускается.\n\n"
                f"URL: {BACKEND_URL}\n\n"
                "Сделай так:\n"
                "1. Закрой все терминалы с uvicorn\n"
                "2. В папке проекта: .\\run_backend.ps1\n"
                "3. Проверь: .\\venv\\Scripts\\python.exe scripts\\verify_backend.py\n"
                "4. Перезапусти бота: .\\run_bot.ps1\n\n"
                f"Ответ сервера: {detail[:200]}"
            )
            return

        await message.answer(f"Ошибка backend ({status}): {detail[:500]}")
        return

    if isinstance(error, RequestError):
        await message.answer(
            "Не могу подключиться к backend.\n\n"
            f"URL: {BACKEND_URL}\n\n"
            "Что проверить:\n"
            "1. В терминале backend должно быть:\n"
            "   Uvicorn running on http://127.0.0.1:8080\n"
            "2. Если видишь ошибку «порт занят» — закрой старый процесс:\n"
            "   netstat -ano | findstr :8000\n"
            "   Stop-Process -Id НОМЕР_PID -Force\n"
            "3. Запусти: .\\run_backend.ps1 (порт 8080)\n"
            "4. Проверь: http://127.0.0.1:8080/health"
        )
        return

    await message.answer("Произошла непредвиденная ошибка. Попробуй позже.")
