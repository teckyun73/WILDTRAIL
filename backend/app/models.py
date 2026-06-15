from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Species(Base):
    __tablename__ = "species"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    common_name: Mapped[str] = mapped_column(String(100), nullable=False)
    scientific_name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="bird")
    protection_grade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    habitat: Mapped[str] = mapped_column(Text, default="")
    diet: Mapped[str] = mapped_column(Text, default="")
    breeding_season: Mapped[str] = mapped_column(String(100), default="")
    active_time: Mapped[str] = mapped_column(String(100), default="")
    observation_tips: Mapped[str] = mapped_column(Text, default="")
    best_months: Mapped[str] = mapped_column(String(50), default="")
    similar_species: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    hotspots: Mapped[list["Hotspot"]] = relationship(back_populates="species")
    sightings: Mapped[list["Sighting"]] = relationship(back_populates="species")


class Hotspot(Base):
    __tablename__ = "hotspots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    region: Mapped[str] = mapped_column(String(100), default="")
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    species_id: Mapped[str] = mapped_column(ForeignKey("species.id"), nullable=False)
    best_months: Mapped[str] = mapped_column(String(50), default="")
    observation_score: Mapped[float] = mapped_column(Float, default=0.0)
    access_level: Mapped[str] = mapped_column(String(50), default="easy")
    transport_note: Mapped[str] = mapped_column(Text, default="")
    entry_fee: Mapped[int] = mapped_column(Integer, default=0)
    facilities: Mapped[str] = mapped_column(Text, default="")
    safety_note: Mapped[str] = mapped_column(Text, default="")

    species: Mapped["Species"] = relationship(back_populates="hotspots")


class Sighting(Base):
    __tablename__ = "sightings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    species_id: Mapped[str] = mapped_column(ForeignKey("species.id"), nullable=False)
    location_name: Mapped[str] = mapped_column(String(200), default="")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    media_type: Mapped[str] = mapped_column(String(20), default="image")
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    species: Mapped["Species"] = relationship(back_populates="sightings")
