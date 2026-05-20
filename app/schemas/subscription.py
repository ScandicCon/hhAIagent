from pydantic import BaseModel


class UsageResponse(BaseModel):
    profile_id: int
    plan: str
    plan_label: str
    searches_per_week: int
    cover_letters_per_week: int
    searches_used: int
    cover_letters_used: int
    searches_left: int
    cover_letters_left: int
    digest_enabled: bool


class DigestToggle(BaseModel):
    enabled: bool


class ActivateProResponse(BaseModel):
    profile_id: int
    plan: str
    plan_label: str
    message: str
