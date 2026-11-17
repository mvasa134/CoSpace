from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.schemas.coworking import Coworking, Workspace
from app.mocks.mock_data import MOCK_COWORKINGS

router = APIRouter(prefix="/coworkings", tags=["coworkings"])

@router.get("", response_model=List[Coworking])
def get_coworkings():
    return MOCK_COWORKINGS

@router.get("/{coworking_id}", response_model=Coworking)
def get_coworking_by_id(coworking_id: int):
    for coworking in MOCK_COWORKINGS:
        if coworking.id == coworking_id:
            return coworking
    raise HTTPException(status_code=404, detail="Коворкінг не знайдено")

@router.get("/{coworking_id}/workspaces", response_model=List[Workspace])
def get_workspaces_by_floor(
    coworking_id: int,
    floor: Optional[int] = Query(None, ge=1, le=7, description="фільтр")
):

    for coworking in MOCK_COWORKINGS:
        if coworking.id == coworking_id:
            if floor is not None:
                return [w for w in coworking.workspaces if w.floor == floor]
            return coworking.workspaces
    raise HTTPException(status_code=404, detail="Коворкінг не знайдено")