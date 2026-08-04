from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_async_db
from services.opportunity_service import get_recommended_opportunities

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("/recommended")
async def recommended_opportunities(
    user_type: str = "",
    looking_for: str = "",
    category: str = "",
    location_preference: str = "",
    db: AsyncSession = Depends(get_async_db)
):
    onboarding_data = {
        "user_type": user_type,
        "looking_for": [x.strip() for x in looking_for.split(",") if x.strip()],
        "category": category,
        "location_preference": location_preference,
    }

    return await get_recommended_opportunities(db, onboarding_data)