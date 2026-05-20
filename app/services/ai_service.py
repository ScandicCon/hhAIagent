from app.schemas.cover_letters import ImprovedCoverLetterResult
from app.schemas.vacancies import AIAnalysisResult, CoverLetterResult
from app.services.ai_client import parse_with_retry


def analyze_vacancy(
    resume: str,
    vacancy_title: str,
    company: str,
    vacancy_description: str,
):
    description = (vacancy_description or "")[:8000]
    prompt = f"""
Ты AI HR assistant.

Твоя задача:
1. Проанализировать насколько кандидат подходит вакансии.
2. Дать оценку от 0 до 100.
3. Выделить сильные стороны.
4. Выделить слабые стороны.
5. Решить стоит ли откликаться.

Резюме кандидата:
{resume}

Название вакансии:
{vacancy_title}

Компания:
{company}

Описание вакансии:
{description}
"""
    return parse_with_retry(AIAnalysisResult, prompt)


def generate_cover_letter(
    resume: str,
    vacancy_title: str,
    company: str,
    vacancy_description: str,
):
    description = (vacancy_description or "")[:8000]
    prompt = f"""
Ты AI HR assistant.

Твоя задача:
1. Проанализировать насколько кандидат подходит вакансию.
2. Проанализировать описание компании.
3. Написать сопроводительное письмо под описание вакансии.
4. Подчеркнуть релевантные навыки кандидата.

Резюме кандидата:
{resume}

Название вакансии:
{vacancy_title}

Компания:
{company}

Описание вакансии:
{description}
"""
    return parse_with_retry(CoverLetterResult, prompt)


def improve_cover_letter(instruction: str, text: str):
    prompt = f"""
Ты AI HR assistant.

Твоя задача:
1. Проанализировать сопроводительное письмо.
2. Проанализировать инструкцию пользователя.
3. Переписать письмо согласно инструкции.
4. Сохранить профессиональный стиль.

Сопроводительное письмо:
{text}

Инструкция пользователя:
{instruction}
"""
    return parse_with_retry(ImprovedCoverLetterResult, prompt)
