from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import ChatRequest, ChatResponse, DocumentAnalysisRequest
from services.gemini_service import ask_gemini, analyze_document

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


def _get_user_profile_dict(db: Session, user_id: str | None):
    if not user_id:
        return None

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return None

    return {
        "name": user.name,
        "age": user.age,
        "category": user.category,
        "income": user.income,
        "occupation": user.occupation,
        "gender": user.gender,
        "state": user.state,
        "current_class": user.current_class,
        "education": user.education,
        "percentage": user.percentage,
    }


@router.post("/general", response_model=ChatResponse)
def general_chat(payload: ChatRequest, db: Session = Depends(get_db)):
    profile = _get_user_profile_dict(db, payload.user_id)
    reply = ask_gemini(payload.message, mode="general", user_profile=profile)
    return {"reply": reply, "mode": "general"}


@router.post("/career", response_model=ChatResponse)
def career_chat(payload: ChatRequest, db: Session = Depends(get_db)):
    profile = _get_user_profile_dict(db, payload.user_id)
    reply = ask_gemini(payload.message, mode="career", user_profile=profile)
    return {"reply": reply, "mode": "career"}


@router.post("/life-event", response_model=ChatResponse)
def life_event_chat(payload: ChatRequest, db: Session = Depends(get_db)):
    profile = _get_user_profile_dict(db, payload.user_id)
    reply = ask_gemini(payload.message, mode="life-event", user_profile=profile)
    return {"reply": reply, "mode": "life-event"}

@router.post("/analyze-document", response_model=ChatResponse)
def analyze_document_endpoint(payload: DocumentAnalysisRequest, db: Session = Depends(get_db)):
    profile = _get_user_profile_dict(db, payload.user_id)
    reply = analyze_document(
        file_data=payload.file_data,
        mime_type=payload.mime_type,
        opportunity_name=payload.opportunity_name,
        user_profile=profile
    )
    return {"reply": reply, "mode": "document-analysis"}