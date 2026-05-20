from pydantic import BaseModel


class PromoRedeemRequest(BaseModel):
    code: str


class PromoRedeemResponse(BaseModel):
    ok: bool
    message: str
    plan: str
    plan_label: str
