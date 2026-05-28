from datetime import datetime

from pydantic import BaseModel, Field

from app.services.apply_modes import APPLY_MODE_SEMI


class DashboardModeUpdate(BaseModel):
    mode: str = Field(..., pattern="^(semi_auto|auto)$")


class DailyStatPoint(BaseModel):
    date: str
    applications: int
    vacancies_found: int


class DashboardStats(BaseModel):
    vacancies_found_today: int
    vacancies_found_delta_pct: int | None = None
    applications_today: int
    applications_delta_pct: int | None = None
    applications_daily_limit: int
    applications_left: int
    active_directions: int
    progress_percent: int
    progress_label: str
    apply_mode: str
    auto_schedule_label: str
    plan_label: str
    searches_left: int
    daily_chart: list[DailyStatPoint]


class VacancyCard(BaseModel):
    analysis_id: int
    hh_id: str
    title: str
    company: str
    url: str
    match_score: int
    should_apply: bool
    summary: str | None = None
    experience: str | None = None
    schedule: str | None = None
    area: str | None = None
    salary: str | None = None
    source_label: str = "HH"
    posted_label: str = "недавно"
    already_applied: bool = False
    created_at: datetime | None = None


class VacancyGroup(BaseModel):
    title: str
    total: int
    vacancies: list[VacancyCard]


class DashboardVacanciesResponse(BaseModel):
    groups: list[VacancyGroup]
    applications_left: int


class DashboardSearchRequest(BaseModel):
    text: str = Field(..., min_length=2, max_length=200)
    per_page: int | None = Field(default=7, ge=1, le=15)


class BatchApplyRequest(BaseModel):
    analysis_ids: list[int] = Field(..., min_length=1, max_length=40)


class BatchApplyItemResult(BaseModel):
    analysis_id: int
    ok: bool
    status: str
    title: str | None = None
    url: str | None = None
    cover_letter: str | None = None
    message: str | None = None


class BatchApplyResponse(BaseModel):
    sent: int
    failed: int
    results: list[BatchApplyItemResult]
    applications_today: int
    applications_left: int


class DashboardMeResponse(BaseModel):
    profile_id: int
    telegram_id: int
    first_name: str | None = None
    username: str | None = None
    resume_ready: bool
    apply_mode: str = APPLY_MODE_SEMI
    plan_label: str
    bot_username: str
