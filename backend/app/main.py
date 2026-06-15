import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.health import build_health_response
from app.logging_config import configure_logging
from app.routers import encyclopedia, identify, locations, sightings, species, trips
from app.schemas import HealthResponse
from app.seed import load_seed_data

configure_logging()

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        report = load_seed_data(db)
        if not report.in_sync:
            logger.warning(
                "Startup check: species.json and DB are out of sync (missing=%s)",
                report.missing_species_ids,
            )
    yield


app = FastAPI(
    title="WildTrail API",
    description="야생동물 식별, 도감, 관찰 위치, 여행 플래너 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(identify.router, prefix="/api/v1")
app.include_router(encyclopedia.router, prefix="/api/v1")
app.include_router(species.router, prefix="/api/v1")
app.include_router(locations.router, prefix="/api/v1")
app.include_router(trips.router, prefix="/api/v1")
app.include_router(sightings.router, prefix="/api/v1")


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    with SessionLocal() as db:
        return build_health_response(db)
