from datetime import datetime

from pydantic import BaseModel


class ResumeVersionItem(BaseModel):
    id: int
    resume_text: str
    created_at: datetime


class ResumeVersionsResponse(BaseModel):
    current: str
    versions: list[ResumeVersionItem]
