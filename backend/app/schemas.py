from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SpeciesSummary(BaseModel):
    id: str
    common_name: str
    scientific_name: str
    category: str
    protection_grade: str | None = None
    best_months: str
    image_url: str | None = None

    model_config = {"from_attributes": True}


class SpeciesDetail(SpeciesSummary):
    habitat: str
    diet: str
    breeding_season: str
    active_time: str
    observation_tips: str
    similar_species: str
    description: str


class IdentificationCandidate(BaseModel):
    species_id: str
    common_name: str
    scientific_name: str
    confidence: float


class IdentificationResult(BaseModel):
    media_type: str
    candidates: list[IdentificationCandidate]
    message: str = ""
    source: Literal["model", "stub"] = "stub"


class HotspotOut(BaseModel):
    id: int
    name: str
    region: str
    latitude: float
    longitude: float
    species_id: str
    species_name: str
    best_months: str
    observation_score: float
    access_level: str
    transport_note: str
    entry_fee: int
    facilities: str
    safety_note: str

    model_config = {"from_attributes": True}


class TripPreferences(BaseModel):
    transport: str = "public"
    accommodation: str = "guesthouse"
    difficulty: str = "easy"


class TripPlanRequest(BaseModel):
    species_id: str
    origin: str = "서울역"
    days: int = Field(default=1, ge=1, le=7)
    budget_krw: int = Field(default=150000, ge=30000)
    travelers: int = Field(default=1, ge=1, le=10)
    month: int | None = Field(default=None, ge=1, le=12)
    preferences: TripPreferences = Field(default_factory=TripPreferences)


class CostBreakdown(BaseModel):
    transport: int
    accommodation: int
    food: int
    entry_fee: int
    misc: int
    total: int
    per_person: int


class TripDayItem(BaseModel):
    time: str
    activity: str
    location: str
    note: str = ""


class TripDayPlan(BaseModel):
    day: int
    title: str
    items: list[TripDayItem]


class TripRouteStop(BaseModel):
    name: str
    role: str
    latitude: float | None = None
    longitude: float | None = None


class TripPlanResponse(BaseModel):
    species_id: str
    species_name: str
    origin: str
    days: int
    travelers: int
    hotspot_name: str
    hotspot_latitude: float
    hotspot_longitude: float
    region: str
    summary: str
    checklist: list[str]
    route_stops: list[TripRouteStop]
    days_plan: list[TripDayPlan]
    costs: CostBreakdown
    disclaimer: str
    source: str


class SightingCreate(BaseModel):
    species_id: str
    location_name: str = ""
    latitude: float | None = None
    longitude: float | None = None
    confidence: float = 0.0
    media_type: str = "image"
    note: str = ""


class SightingOut(SightingCreate):
    id: int
    common_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EncyclopediaAskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    species_id: str | None = None


class Citation(BaseModel):
    chunk_id: str
    title: str
    source: str
    species_id: str | None = None


class EncyclopediaAskResponse(BaseModel):
    question: str
    species_id: str | None
    answer: str
    citations: list[Citation]
    source: str


class MapLocation(BaseModel):
    id: int
    name: str
    region: str
    latitude: float
    longitude: float
    species_id: str
    species_name: str
    observation_score: float
    entry_fee: int
    transport_note: str


class RegionInfoResponse(BaseModel):
    region: str
    weather: dict
    transport: dict
    tourism: dict


class ModelStatus(BaseModel):
    model_loaded: bool
    model_classes: int = 0
    model_val_acc: float | None = None
    model_path: str = ""
    model_version: str | None = None
    trained_at: str | None = None
    backbone: str | None = None
    preprocess_version: str | None = None
    dataset_fingerprint: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str
    image_model: ModelStatus
    audio_model: ModelStatus
    species_json_count: int
    species_db_count: int
    llm_configured: bool
    llm_provider: str
    llm_model: str
    warnings: list[str] = Field(default_factory=list)
