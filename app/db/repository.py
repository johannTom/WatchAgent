from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Event, Reading


def count_readings(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Reading)) or 0


def count_events(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Event)) or 0


def store_reading_if_new(
    db: Session,
    *,
    city: str,
    observed_at: datetime,
    temperature_2m: float,
    apparent_temperature: float,
    precipitation: float,
    wind_speed_10m: float,
    weather_code: int,
) -> Reading | None:
    existing = db.scalar(
        select(Reading.id).where(
            Reading.city == city,
            Reading.observed_at == observed_at,
        )
    )
    if existing is not None:
        return None  # already stored for this city + timestamp

    reading = Reading(
        city=city,
        observed_at=observed_at,
        temperature_2m=temperature_2m,
        apparent_temperature=apparent_temperature,
        precipitation=precipitation,
        wind_speed_10m=wind_speed_10m,
        weather_code=weather_code,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading
