from pydantic import BaseModel

class ProfileCreate(BaseModel):
    name: str
    resume_text: str
    skills: str
    referral_code: str | None = None

class ProfileResponse(BaseModel):
    id: int
    name: str
    resume_text: str
    skills: str | None = None