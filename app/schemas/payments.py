from pydantic import BaseModel


class PaymentCreateResponse(BaseModel):
    payment_id: int
    confirmation_url: str
    amount_rub: int


class ReferralApplyRequest(BaseModel):
    referral_code: str


class ReferralInfoResponse(BaseModel):
    referral_code: str
    referral_link: str
    invited_count: int
    bonus_searches: int
    reward_per_friend: int
