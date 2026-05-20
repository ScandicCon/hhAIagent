from pydantic import BaseModel
from datetime import datetime


class VacancyAnalysisCreate(BaseModel):
    profile_id: int
    vacancy_id: int
    match_score: int
    should_apply: bool
    summary: str
    pros: list[str]
    cons: list[str]


class VacancyAnalysisResponse(BaseModel):
    id: int

    profile_id: int
    vacancy_id: int

    match_score: int
    should_apply: bool

    summary: str

    pros: list[str]
    cons: list[str]

    created_at: datetime