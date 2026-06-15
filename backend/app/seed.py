import json
import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Hotspot, Species

settings = get_settings()
logger = logging.getLogger(__name__)

SPECIES_FIELDS = (
    "common_name",
    "scientific_name",
    "category",
    "protection_grade",
    "habitat",
    "diet",
    "breeding_season",
    "active_time",
    "observation_tips",
    "best_months",
    "similar_species",
    "description",
    "image_url",
)

HOTSPOT_FIELDS = (
    "name",
    "region",
    "latitude",
    "longitude",
    "species_id",
    "best_months",
    "observation_score",
    "access_level",
    "transport_note",
    "entry_fee",
    "facilities",
    "safety_note",
)


@dataclass
class SeedSyncReport:
    species_inserted: int = 0
    species_updated: int = 0
    hotspots_inserted: int = 0
    hotspots_updated: int = 0
    species_json_count: int = 0
    species_db_count: int = 0
    hotspots_json_count: int = 0
    hotspots_db_count: int = 0
    missing_species_ids: list[str] = field(default_factory=list)
    extra_species_ids: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def in_sync(self) -> bool:
        return not self.missing_species_ids and self.species_json_count == self.species_db_count


def _load_json(path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


SPECIES_OPTIONAL_NULL_FIELDS = {"protection_grade", "image_url"}


def _apply_fields(model, data: dict, fields: tuple[str, ...], optional_null: set[str] | None = None) -> None:
    optional_null = optional_null or set()
    for key in fields:
        if key not in data:
            continue
        value = data[key]
        if value is None and key not in optional_null:
            value = ""
        setattr(model, key, value)


def _hotspot_key(item: dict) -> tuple[str, str, float, float]:
    return (
        item["name"],
        item["species_id"],
        round(float(item["latitude"]), 6),
        round(float(item["longitude"]), 6),
    )


def sync_species(db: Session, species_data: list[dict]) -> tuple[int, int]:
    inserted = 0
    updated = 0

    for item in species_data:
        species_id = item["id"]
        existing = db.get(Species, species_id)
        if existing:
            _apply_fields(existing, item, SPECIES_FIELDS, SPECIES_OPTIONAL_NULL_FIELDS)
            updated += 1
        else:
            payload = {k: item.get(k) for k in SPECIES_FIELDS}
            for key in SPECIES_FIELDS:
                if payload.get(key) is None and key not in SPECIES_OPTIONAL_NULL_FIELDS:
                    payload[key] = ""
            db.add(Species(id=species_id, **payload))
            inserted += 1

    db.flush()
    return inserted, updated


def sync_hotspots(db: Session, hotspots_data: list[dict]) -> tuple[int, int]:
    inserted = 0
    updated = 0

    existing_rows = db.query(Hotspot).all()
    index = {
        (
            row.name,
            row.species_id,
            round(float(row.latitude), 6),
            round(float(row.longitude), 6),
        ): row
        for row in existing_rows
    }

    for item in hotspots_data:
        key = _hotspot_key(item)
        existing = index.get(key)
        if existing:
            _apply_fields(existing, item, HOTSPOT_FIELDS)
            updated += 1
        else:
            db.add(Hotspot(**{k: item[k] for k in HOTSPOT_FIELDS}))
            inserted += 1

    db.flush()
    return inserted, updated


def validate_species_sync(db: Session, species_data: list[dict]) -> tuple[list[str], list[str], list[str]]:
    json_ids = {item["id"] for item in species_data}
    db_ids = {row.id for row in db.query(Species.id).all()}

    missing = sorted(json_ids - db_ids)
    extra = sorted(db_ids - json_ids)
    warnings: list[str] = []

    if missing:
        warnings.append(f"species.json에 있으나 DB에 없는 종: {', '.join(missing)}")
    if extra:
        warnings.append(f"DB에만 존재하는 종(JSON에 없음): {', '.join(extra)}")
    if len(json_ids) != len(db_ids):
        warnings.append(
            f"species 수 불일치: json={len(json_ids)}, db={len(db_ids)}"
        )

    return missing, extra, warnings


def load_seed_data(db: Session) -> SeedSyncReport:
    species_file = settings.data_dir / "species.json"
    hotspots_file = settings.data_dir / "hotspots.json"

    species_data = _load_json(species_file)
    hotspots_data = _load_json(hotspots_file)

    species_inserted, species_updated = sync_species(db, species_data)
    hotspots_inserted, hotspots_updated = sync_hotspots(db, hotspots_data)
    db.commit()

    missing, extra, warnings = validate_species_sync(db, species_data)

    report = SeedSyncReport(
        species_inserted=species_inserted,
        species_updated=species_updated,
        hotspots_inserted=hotspots_inserted,
        hotspots_updated=hotspots_updated,
        species_json_count=len(species_data),
        species_db_count=db.query(Species).count(),
        hotspots_json_count=len(hotspots_data),
        hotspots_db_count=db.query(Hotspot).count(),
        missing_species_ids=missing,
        extra_species_ids=extra,
        warnings=warnings,
    )

    log_seed_sync_report(report)
    return report


def log_seed_sync_report(report: SeedSyncReport) -> None:
    logger.info(
        "Seed sync: species inserted=%s updated=%s (json=%s db=%s), "
        "hotspots inserted=%s updated=%s (json=%s db=%s)",
        report.species_inserted,
        report.species_updated,
        report.species_json_count,
        report.species_db_count,
        report.hotspots_inserted,
        report.hotspots_updated,
        report.hotspots_json_count,
        report.hotspots_db_count,
    )
    for warning in report.warnings:
        logger.warning("Seed sync warning: %s", warning)
    if report.in_sync:
        logger.info("Species metadata is in sync with species.json")
    else:
        logger.warning("Species metadata is NOT fully in sync with species.json")
