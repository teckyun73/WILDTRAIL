from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Species
from app.schemas import SpeciesDetail, SpeciesSummary

router = APIRouter(prefix="/species", tags=["species"])


@router.get("", response_model=list[SpeciesSummary])
def list_species(
    q: str | None = Query(default=None, description="국명/학명 검색"),
    db: Session = Depends(get_db),
) -> list[Species]:
    query = db.query(Species)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Species.common_name.like(like)) | (Species.scientific_name.like(like))
        )
    return query.order_by(Species.common_name).all()


@router.get("/{species_id}", response_model=SpeciesDetail)
def get_species(species_id: str, db: Session = Depends(get_db)) -> Species:
    species = db.get(Species, species_id)
    if not species:
        raise HTTPException(status_code=404, detail="종을 찾을 수 없습니다.")
    return species
