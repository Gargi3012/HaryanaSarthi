from sqlalchemy.orm import Session
from models import OnboardingData
from schemas import SaveStepRequest


def create_session(db: Session, session_id: str):
    existing = db.query(OnboardingData).filter(OnboardingData.session_id == session_id).first()
    if existing:
        return existing

    session = OnboardingData(session_id=session_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_onboarding_data(db: Session, session_id: str):
    return db.query(OnboardingData).filter(OnboardingData.session_id == session_id).first()


def save_step(db: Session, session_id: str, payload: SaveStepRequest):
    data = get_onboarding_data(db, session_id)
    if not data:
        return None

    if payload.step_number == 1:
        if payload.user_type is not None:
            data.user_type = str(payload.user_type)
        data.step1_completed = not payload.is_skipped
        data.step1_skipped = payload.is_skipped

    elif payload.step_number == 2:
        if payload.looking_for is not None:
            if isinstance(payload.looking_for, list):
                data.looking_for = ", ".join([str(x) for x in payload.looking_for])
            else:
                data.looking_for = str(payload.looking_for)
        data.step2_completed = not payload.is_skipped
        data.step2_skipped = payload.is_skipped

    elif payload.step_number == 3:
        if payload.category is not None:
            data.category = str(payload.category)
        data.step3_completed = not payload.is_skipped
        data.step3_skipped = payload.is_skipped

    elif payload.step_number == 4:
        if payload.location_preference is not None:
            data.location_preference = str(payload.location_preference)
        data.step4_completed = not payload.is_skipped
        data.step4_skipped = payload.is_skipped

    db.commit()
    db.refresh(data)
    return data


def complete_onboarding(db: Session, session_id: str):
    data = get_onboarding_data(db, session_id)
    if not data:
        return False
    db.commit()
    return True