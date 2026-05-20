from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.profiles import Profile
from app.schemas.payments import ReferralApplyRequest, ReferralInfoResponse
from app.services.referrals import apply_referral, get_referral_info

router = APIRouter(prefix="/referrals", tags=["referrals"])


def _get_profile(profile_id: int, session: Session) -> Profile:
    profile = session.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get("/info/{profile_id}", response_model=ReferralInfoResponse)
def referral_info(profile_id: int, session: Session = Depends(get_db)):
    profile = _get_profile(profile_id, session)
    info = get_referral_info(profile, session)
    return ReferralInfoResponse(**info)


@router.post("/apply/{profile_id}")
def referral_apply(
    profile_id: int,
    body: ReferralApplyRequest,
    session: Session = Depends(get_db),
):
    profile = _get_profile(profile_id, session)
    result = apply_referral(profile, body.referral_code, session)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result
