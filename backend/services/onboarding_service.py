from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import OnboardingData
from schemas import SaveStepRequest


async def create_session(db: AsyncSession, session_id: str):
    query = select(OnboardingData).where(OnboardingData.session_id == session_id)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    session = OnboardingData(session_id=session_id)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_onboarding_data(db: AsyncSession, session_id: str):
    query = select(OnboardingData).where(OnboardingData.session_id == session_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def save_step(db: AsyncSession, session_id: str, payload: SaveStepRequest):
    data = await get_onboarding_data(db, session_id)
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

    await db.commit()
    await db.refresh(data)
    return data


async def complete_onboarding(db: AsyncSession, session_id: str):
    data = await get_onboarding_data(db, session_id)
    if not data:
        return False
    await db.commit()
    return True