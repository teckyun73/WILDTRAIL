from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Sighting, Species
from app.schemas import SightingCreate, SightingOut

router = APIRouter(prefix="/sightings", tags=["sightings"])


@router.get("", response_model=list[SightingOut])
def list_sightings(db: Session = Depends(get_db)) -> list[SightingOut]:
    rows = (
        db.query(Sighting, Species)
        .join(Species, Sighting.species_id == Species.id)
        .order_by(Sighting.created_at.desc())
        .all()
    )
    return [
        SightingOut(
            id=sighting.id,
            species_id=sighting.species_id,
            common_name=species.common_name,
            location_name=sighting.location_name,
            latitude=sighting.latitude,
            longitude=sighting.longitude,
            confidence=sighting.confidence,
            media_type=sighting.media_type,
            note=sighting.note,
            created_at=sighting.created_at,
        )
        for sighting, species in rows
    ]


@router.post("", response_model=SightingOut)
def create_sighting(payload: SightingCreate, db: Session = Depends(get_db)) -> SightingOut:
    species = db.get(Species, payload.species_id)
    if not species:
        raise HTTPException(status_code=404, detail="종을 찾을 수 없습니다.")

    sighting = Sighting(**payload.model_dump())
    db.add(sighting)
    db.commit()
    db.refresh(sighting)

    return SightingOut(
        id=sighting.id,
        species_id=sighting.species_id,
        common_name=species.common_name,
        location_name=sighting.location_name,
        latitude=sighting.latitude,
        longitude=sighting.longitude,
        confidence=sighting.confidence,
        media_type=sighting.media_type,
        note=sighting.note,
        created_at=sighting.created_at,
    )
