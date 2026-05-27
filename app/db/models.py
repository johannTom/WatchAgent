from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city: Mapped[str] = mapped_column(String(64), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    temperature_2m: Mapped[float] = mapped_column(Float)
    apparent_temperature: Mapped[float] = mapped_column(Float)
    precipitation: Mapped[float] = mapped_column(Float)
    wind_speed_10m: Mapped[float] = mapped_column(Float)
    weather_code: Mapped[int] = mapped_column(Integer)

    __table_args__ = (
        UniqueConstraint("city", "observed_at", name="uq_reading_city_observed_at"),
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city: Mapped[str] = mapped_column(String(64), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    summary: Mapped[str] = mapped_column(String(256))
    reason: Mapped[str] = mapped_column(Text)
