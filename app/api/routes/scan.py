from fastapi import APIRouter, Depends

from app.api.deps import get_checkpointer
from app.graph import run_scan
from app.schemas.scan import ScanSummary

router = APIRouter(tags=["scan"])


@router.post("/scan", response_model=ScanSummary)
def trigger_scan(checkpointer=Depends(get_checkpointer)):
    return run_scan(checkpointer)
