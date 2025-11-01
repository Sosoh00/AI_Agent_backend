from fastapi import APIRouter, Depends, HTTPException
from services import mt5_service
from schemas import AccountInformationResponse


from auth import get_current_user


router = APIRouter(prefix="/account", tags=["Account"])

@router.get("/information", response_model=AccountInformationResponse, description="Get extended account info including leverage, margin, currency, and balance.")
def get_account_information():
    info = mt5_service.get_account_information()
    if not info:
        raise HTTPException(status_code=500, detail="Failed to retrieve account information")
    return info