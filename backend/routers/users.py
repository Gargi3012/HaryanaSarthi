from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_async_db
from models import User
from services.auth_service import get_current_user

router = APIRouter(tags=["users"])


@router.get("/user/{user_id}")
async def get_user_profile(
    user_id: str, 
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    # Authorization check to prevent BOLA (Broken Object Level Authorization)
    if current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this profile."
        )

    # Since get_current_user has already loaded current_user, return it directly to save a query
    return {
        "user_id": current_user.user_id,
        "name": current_user.name,
        "age": current_user.age,
        "category": current_user.category,
        "income": current_user.income,
        "occupation": current_user.occupation,
        "caste": current_user.caste,
        "divyang": current_user.divyang,
        "gender": current_user.gender,
        "state": current_user.state,
        "current_class": current_user.current_class,
        "education": current_user.education,
        "percentage": current_user.percentage,
    }