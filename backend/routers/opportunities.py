from fastapi import APIRouter, HTTPException
from services.opportunity_service import get_recommended_opportunities

router = APIRouter(prefix="/opportunities", tags=["opportunities"])

# temporary in-memory onboarding fallback from localStorage style flow
# if your onboarding DB/session route already exists, keep it simple here


@router.get("/recommended")
def recommended_opportunities(
    user_type: str = "",
    looking_for: str = "",
    category: str = "",
    location_preference: str = "",
):
    onboarding_data = {
        "user_type": user_type,
        "looking_for": [x.strip() for x in looking_for.split(",") if x.strip()],
        "category": category,
        "location_preference": location_preference,
    }

    return get_recommended_opportunities(onboarding_data)