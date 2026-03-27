from fastapi import APIRouter
from services.dataset_loader import dataset_loader

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
def get_stats():
    colleges_df = dataset_loader.get("colleges")

    return {
        "colleges": len(colleges_df) if not colleges_df.empty else 0,
        "jobs_exams": 0,
        "scholarships": 0,
        "internships": 0,
        "schemes": 0,
    }