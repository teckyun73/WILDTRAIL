from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import EncyclopediaAskRequest, EncyclopediaAskResponse
from app.services.rag import encyclopedia_rag_service

router = APIRouter(prefix="/encyclopedia", tags=["encyclopedia"])


@router.post("/ask", response_model=EncyclopediaAskResponse)
def ask_encyclopedia(
    payload: EncyclopediaAskRequest,
    db: Session = Depends(get_db),
) -> EncyclopediaAskResponse:
    try:
        result = encyclopedia_rag_service.ask(
            db, question=payload.question, species_id=payload.species_id
        )
        return EncyclopediaAskResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
