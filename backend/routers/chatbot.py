import uuid
from fastapi import APIRouter, Depends, status, Request, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_async_db
from models import User
from schemas import ChatRequest, ChatResponse, DocumentAnalysisRequest
from services.gemini_service import ask_llm, analyze_document_async
from services.redis_service import redis_service

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# Memory-backed task store for asynchronous document processing jobs
analysis_tasks = {}


async def _get_user_profile_dict(db: AsyncSession, user_id: str | None):
    if not user_id:
        return None

    query = select(User).where(User.user_id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
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


def _check_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not redis_service.check_rate_limit(client_ip, limit=10, window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many messages sent. Please wait a minute and try again."
        )


async def run_document_analysis_task(task_id: str, file_data: str, mime_type: str, opportunity_name: str, profile: dict):
    try:
        reply = await analyze_document_async(
            file_data=file_data,
            mime_type=mime_type,
            opportunity_name=opportunity_name,
            user_profile=profile
        )
        analysis_tasks[task_id] = {"status": "completed", "reply": reply}
    except Exception as e:
        print(f"[ASYNC TASK ERROR] {e}")
        analysis_tasks[task_id] = {"status": "failed", "reply": "An error occurred during document parsing."}


@router.post("/general", response_model=ChatResponse)
async def general_chat(request: Request, payload: ChatRequest, db: AsyncSession = Depends(get_async_db)):
    _check_rate_limit(request)
    profile = await _get_user_profile_dict(db, payload.user_id)
    reply = await ask_llm(payload.message, mode="general", user_profile=profile)
    return {"reply": reply, "mode": "general"}


@router.post("/career", response_model=ChatResponse)
async def career_chat(request: Request, payload: ChatRequest, db: AsyncSession = Depends(get_async_db)):
    _check_rate_limit(request)
    profile = await _get_user_profile_dict(db, payload.user_id)
    reply = await ask_llm(payload.message, mode="career", user_profile=profile)
    return {"reply": reply, "mode": "career"}


@router.post("/life-event", response_model=ChatResponse)
async def life_event_chat(request: Request, payload: ChatRequest, db: AsyncSession = Depends(get_async_db)):
    _check_rate_limit(request)
    profile = await _get_user_profile_dict(db, payload.user_id)
    reply = await ask_llm(payload.message, mode="life-event", user_profile=profile)
    return {"reply": reply, "mode": "life-event"}


@router.post("/analyze-document", response_model=ChatResponse)
async def analyze_document_endpoint(request: Request, payload: DocumentAnalysisRequest, db: AsyncSession = Depends(get_async_db)):
    _check_rate_limit(request)
    profile = await _get_user_profile_dict(db, payload.user_id)
    reply = await analyze_document_async(
        file_data=payload.file_data,
        mime_type=payload.mime_type,
        opportunity_name=payload.opportunity_name,
        user_profile=profile
    )
    return {"reply": reply, "mode": "document-analysis"}


@router.post("/analyze-document/async")
async def analyze_document_async_endpoint(
    request: Request,
    payload: DocumentAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
):
    _check_rate_limit(request)
    profile = await _get_user_profile_dict(db, payload.user_id)
    
    # Generate unique task id
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    analysis_tasks[task_id] = {"status": "processing", "reply": None}
    
    # Add slow document analysis task to background execution thread
    background_tasks.add_task(
        run_document_analysis_task,
        task_id=task_id,
        file_data=payload.file_data,
        mime_type=payload.mime_type,
        opportunity_name=payload.opportunity_name,
        profile=profile
    )
    
    return {"task_id": task_id, "status": "processing"}


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    task = analysis_tasks.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Asynchronous document analysis task not found."
        )
    return task