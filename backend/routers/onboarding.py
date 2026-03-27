import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas import SaveStepRequest
from services.onboarding_service import (
    create_session,
    get_onboarding_data,
    save_step,
    complete_onboarding
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/session/create")
def create_onboarding_session(db: Session = Depends(get_db)):
    session_id = f"session_{uuid.uuid4().hex[:10]}"
    create_session(db, session_id)
    return {
        "session_id": session_id,
        "message": "Session created successfully"
    }


@router.get("/session/{session_id}")
def get_onboarding_session(session_id: str, db: Session = Depends(get_db)):
    data = get_onboarding_data(db, session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")

    looking_for = []
    if data.looking_for:
        looking_for = [x.strip() for x in data.looking_for.split(",") if x.strip()]

    return {
        "session_id": data.session_id,
        "user_type": data.user_type,
        "looking_for": looking_for,
        "category": data.category,
        "location_preference": data.location_preference,
        "step1_completed": data.step1_completed,
        "step2_completed": data.step2_completed,
        "step3_completed": data.step3_completed,
        "step4_completed": data.step4_completed,
        "step1_skipped": data.step1_skipped,
        "step2_skipped": data.step2_skipped,
        "step3_skipped": data.step3_skipped,
        "step4_skipped": data.step4_skipped,
    }


@router.post("/session/{session_id}/save-step")
def save_onboarding_step(session_id: str, payload: SaveStepRequest, db: Session = Depends(get_db)):
    data = save_step(db, session_id, payload)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Step saved successfully", "session_id": session_id}


@router.post("/session/{session_id}/complete")
def complete_onboarding_session(session_id: str, db: Session = Depends(get_db)):
    success = complete_onboarding(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Onboarding completed successfully", "session_id": session_id}