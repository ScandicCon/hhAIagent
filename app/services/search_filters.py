import json
from typing import Any

from pydantic import BaseModel

GRADE_LABELS = {
    "junior": "Junior",
    "middle": "Middle",
    "senior": "Senior",
    "intern": "Стажёр",
}

GRADE_QUERY_PARTS = {
    "junior": "junior OR младший",
    "middle": "middle OR мидл OR middle",
    "senior": "senior OR старший OR lead",
    "intern": "стажёр OR intern OR internship",
}

EXPERIENCE_LABELS = {
    "noExperience": "Без опыта",
    "between1And3": "1–3 года",
    "between3And6": "3–6 лет",
    "moreThan6": "6+ лет",
}

SCHEDULE_LABELS = {
    "remote": "Удалённо",
    "office": "Офис / гибрид",
}

SALARY_LABELS = {
    100000: "от 100 000 ₽",
    150000: "от 150 000 ₽",
    200000: "от 200 000 ₽",
    250000: "от 250 000 ₽",
}


class VacancySearchFilters(BaseModel):
    grade: str | None = None
    experience: str | None = None
    schedule: str | None = None
    area_id: int | None = None
    area_name: str | None = None
    salary_from: int | None = None
    only_with_salary: bool = False

    def is_empty(self) -> bool:
        return not any([
            self.grade,
            self.experience,
            self.schedule,
            self.area_id,
            self.salary_from,
            self.only_with_salary,
        ])

    def signature(self) -> str:
        return json.dumps(self.model_dump(), sort_keys=True)

    def summary_lines(self) -> list[str]:
        lines = []
        if self.grade:
            lines.append(f"Уровень: {GRADE_LABELS.get(self.grade, self.grade)}")
        if self.experience:
            lines.append(f"Опыт в вакансии: {EXPERIENCE_LABELS.get(self.experience, self.experience)}")
        if self.schedule:
            lines.append(f"Формат: {SCHEDULE_LABELS.get(self.schedule, self.schedule)}")
        if self.area_name:
            lines.append(f"Город: {self.area_name}")
        if self.salary_from:
            label = SALARY_LABELS.get(self.salary_from, f"от {self.salary_from:,} ₽".replace(",", " "))
            lines.append(f"Зарплата: {label}")
        elif self.only_with_salary:
            lines.append("Зарплата: только с указанной")
        return lines or ["Фильтры: без ограничений"]


def build_search_text(base_text: str, filters: VacancySearchFilters | None) -> str:
    text = (base_text or "").strip()
    if not filters or not filters.grade:
        return text

    extra = GRADE_QUERY_PARTS.get(filters.grade)
    if not extra:
        return text

    return f"{text} ({extra})"


def build_hh_search_params(
    base_text: str,
    filters: VacancySearchFilters | None,
    *,
    per_page: int,
    page: int,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "text": build_search_text(base_text, filters),
        "per_page": per_page,
        "page": page,
    }

    if filters:
        if filters.experience:
            params["experience"] = filters.experience
        if filters.schedule == "remote":
            params["schedule"] = "remote"
        elif filters.schedule == "office":
            params["schedule"] = "fullDay"
        if filters.area_id:
            params["area"] = filters.area_id
        if filters.salary_from:
            params["salary"] = filters.salary_from
        if filters.only_with_salary:
            params["only_with_salary"] = "true"

    return params


def parse_filters_json(raw: str | None) -> VacancySearchFilters | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return VacancySearchFilters.model_validate(data)
    except (json.JSONDecodeError, ValueError):
        return None


def filters_to_json(filters: VacancySearchFilters | None) -> str | None:
    if filters is None or filters.is_empty():
        return None
    return filters.model_dump_json()
