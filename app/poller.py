# Name: Johan Tom Chacko
# Date: 2026-05-28
# What this file does: pulls weather from Open-Meteo every few minutes and saves new readings.

import asyncio
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy.orm import Session

from app.config import CITIES, CURRENT_FIELDS, OPEN_METEO_URL, POLL_INTERVAL_SECONDS
from app.db.repository import store_reading_if_new
from app.db.session import SessionLocal
from app.events import evaluate_reading

logger = logging.getLogger(__name__)


def _to_utc(time_value: str, timezone_name: str) -> datetime:
    # Open-Meteo gives local time without a +00:00 style offset when timezone=auto
    observed_at = datetime.fromisoformat(time_value)
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=ZoneInfo(timezone_name))
    return observed_at.astimezone(timezone.utc)


def fetch_current_weather(client: httpx.Client, city_name: str, latitude: float, longitude: float) -> dict:
    response = client.get(
        OPEN_METEO_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": ",".join(CURRENT_FIELDS),
            "wind_speed_unit": "kmh",
            "timezone": "auto",
        },
        timeout=30.0,
    )
    response.raise_for_status()
    payload = response.json()
    current = payload["current"]
    return {
        "city": city_name,
        "observed_at": _to_utc(current["time"], payload.get("timezone", "UTC")),
        "temperature_2m": float(current["temperature_2m"]),
        "apparent_temperature": float(current["apparent_temperature"]),
        "precipitation": float(current["precipitation"]),
        "wind_speed_10m": float(current["wind_speed_10m"]),
        "weather_code": int(current["weather_code"]),
    }


def poll_city(db: Session, client: httpx.Client, city_name: str, latitude: float, longitude: float) -> None:
    try:
        weather = fetch_current_weather(client, city_name, latitude, longitude)
        reading = store_reading_if_new(db, **weather)
        if reading is None:
            return  # same timestamp as last time — nothing new to store
        evaluate_reading(db, reading)
        logger.info("Stored reading for %s at %s", city_name, reading.observed_at.isoformat())
    except httpx.HTTPError as exc:
        logger.warning("Weather fetch failed for %s: %s", city_name, exc)
    except Exception:
        db.rollback()
        logger.exception("Poll failed for %s", city_name)


def poll_all_cities() -> None:
    db = SessionLocal()
    try:
        with httpx.Client() as client:
            for city in CITIES:
                poll_city(db, client, city.name, city.latitude, city.longitude)
    finally:
        db.close()


async def poller_loop() -> None:
    logger.info("Weather poller started (interval=%ss)", POLL_INTERVAL_SECONDS)
    while True:
        try:
            await asyncio.to_thread(poll_all_cities)
        except Exception:
            logger.exception("Poll cycle failed")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
