from pydantic import BaseModel


class HhConnectionStatus(BaseModel):
    connected: bool
    resume_id: str | None = None
    resume_title: str | None = None
    auto_apply_enabled: bool
    applications_today: int
    applications_daily_limit: int


class HhResumeItem(BaseModel):
    id: str
    title: str | None = None
    url: str | None = None


class HhSyncResumeRequest(BaseModel):
    resume_id: str | None = None


class HhSyncResumeResponse(BaseModel):
    resume_id: str
    resume_title: str | None = None
    resume_text_length: int
    resumes_available: int


class HhApplyRequest(BaseModel):
    message: str | None = None


class HhAutoApplyToggle(BaseModel):
    enabled: bool


class HhApplyResponse(BaseModel):
    ok: bool
    already_applied: bool = False
    vacancy_hh_id: str
    applications_today: int | None = None
