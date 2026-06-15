from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Hotspot, Species
from app.schemas import HotspotOut, MapLocation, RegionInfoResponse
from app.services.public_api import public_api_service

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=list[HotspotOut])
def list_locations(
    species_id: str | None = Query(default=None),
    month: int | None = Query(default=None, ge=1, le=12),
    access_level: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[HotspotOut]:
    query = db.query(Hotspot, Species).join(Species, Hotspot.species_id == Species.id)
    if species_id:
        query = query.filter(Hotspot.species_id == species_id)
    if access_level:
        query = query.filter(Hotspot.access_level == access_level)

    results: list[HotspotOut] = []
    for hotspot, species in query.order_by(Hotspot.observation_score.desc()).all():
        if month and str(month) not in hotspot.best_months.split(","):
            continue
        results.append(
            HotspotOut(
                id=hotspot.id,
                name=hotspot.name,
                region=hotspot.region,
                latitude=hotspot.latitude,
                longitude=hotspot.longitude,
                species_id=hotspot.species_id,
                species_name=species.common_name,
                best_months=hotspot.best_months,
                observation_score=hotspot.observation_score,
                access_level=hotspot.access_level,
                transport_note=hotspot.transport_note,
                entry_fee=hotspot.entry_fee,
                facilities=hotspot.facilities,
                safety_note=hotspot.safety_note,
            )
        )
    return results


@router.get("/map", response_model=list[MapLocation])
def map_locations(
    species_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[MapLocation]:
    query = db.query(Hotspot, Species).join(Species, Hotspot.species_id == Species.id)
    if species_id:
        query = query.filter(Hotspot.species_id == species_id)
    return [
        MapLocation(
            id=hotspot.id,
            name=hotspot.name,
            region=hotspot.region,
            latitude=hotspot.latitude,
            longitude=hotspot.longitude,
            species_id=hotspot.species_id,
            species_name=species.common_name,
            observation_score=hotspot.observation_score,
            entry_fee=hotspot.entry_fee,
            transport_note=hotspot.transport_note,
        )
        for hotspot, species in query.order_by(Hotspot.observation_score.desc()).all()
    ]


@router.get("/region-info", response_model=RegionInfoResponse)
def region_info(region: str = Query(..., min_length=2)) -> RegionInfoResponse:
    return RegionInfoResponse(
        region=region,
        weather=public_api_service.get_weather_stub(region),
        transport=public_api_service.get_nearby_transport_stub(region),
        tourism=public_api_service.get_tourism_stub(region),
    )
