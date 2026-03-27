from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User

router = APIRouter(tags=["users"])


@router.get("/user/{user_id}")
def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user.user_id,
        "name": user.name,
        "age": user.age,
        "category": user.category,
        "income": user.income,
        "occupation": user.occupation,
        "caste": user.caste,
        "divyang": user.divyang,
        "gender": user.gender,
        "state": user.state,
        "current_class": user.current_class,
        "education": user.education,
        "percentage": user.percentage,
    }