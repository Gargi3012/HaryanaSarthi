from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == payload.user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if str(user.password_hash).strip() != str(payload.password).strip():
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "user_id": user.user_id,
        "name": user.name,
        "category": user.category,
    }