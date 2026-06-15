from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import TripPlanRequest, TripPlanResponse
from app.services.trip_planner import trip_planner_service

router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("/plan", response_model=TripPlanResponse)
def plan_trip(request: TripPlanRequest, db: Session = Depends(get_db)) -> TripPlanResponse:
    try:
        return trip_planner_service.plan(db, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
