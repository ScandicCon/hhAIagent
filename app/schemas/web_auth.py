from pydantic import BaseModel


class TelegramLoginPayload(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    profile_id: int
    telegram_id: int
    resume_ready: bool
