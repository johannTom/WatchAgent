# Name: Johan Tom Chacko
# Date: 2026-05-28
# What this file does: starts FastAPI, runs the poller in the background, and serves /health, /readings, /events.

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query
from sqlalchemy.orm import Session

from app.config import ENABLE_POLLER
from app.db.models import Event, Reading
from app.db.repository import count_events, count_readings, list_events, list_readings
from app.db.session import get_db, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    poller_task = None
    if ENABLE_POLLER:
        from app.poller import poller_loop

        poller_task = asyncio.create_task(poller_loop())
    try:
        yield
    finally:
        if poller_task is not None:
            poller_task.cancel()
            try:
                await poller_task
            except asyncio.CancelledError:
                pass


app = FastAPI(lifespan=lifespan)


def serialize_reading(reading: Reading) -> dict:
    return {
        "id": reading.id,
        "city": reading.city,
        "observed_at": reading.observed_at,
        "temperature_2m": reading.temperature_2m,
        "apparent_temperature": reading.apparent_temperature,
        "precipitation": reading.precipitation,
        "wind_speed_10m": reading.wind_speed_10m,
        "weather_code": reading.weather_code,
    }


def serialize_event(event: Event) -> dict:
    return {
        "id": event.id,
        "city": event.city,
        "observed_at": event.observed_at,
        "event_type": event.event_type,
        "summary": event.summary,
        "reason": event.reason,
    }


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    return {
        "status": "ok",
        "readings_stored": count_readings(db),
        "events_stored": count_events(db),
    }


@app.get("/readings")
def readings(
    db: Session = Depends(get_db),
    city: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
) -> dict:
    return {
        "readings": [
            serialize_reading(reading) for reading in list_readings(db, city=city, limit=limit)
        ]
    }


@app.get("/events")
def events(
    db: Session = Depends(get_db),
    city: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
) -> dict:
    return {
        "events": [serialize_event(event) for event in list_events(db, city=city, limit=limit)]
    }
