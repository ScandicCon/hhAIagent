from pydantic import BaseModel, Field

from app.schemas.subscription import UsageResponse
from app.services.search_filters import VacancySearchFilters


class VacancySearchRequest(BaseModel):
    text: str
    per_page: int = 10
    filters: VacancySearchFilters | None = None


class AIAnalysisResult(BaseModel):
    match_score: int
    should_apply: bool
    pros: list[str]
    cons: list[str]
    summary: str


class CoverLetterResult(BaseModel):
    cover_letter: str


class VacancySearchResponse(BaseModel):
    vacancies: list[dict]
    usage: UsageResponse
