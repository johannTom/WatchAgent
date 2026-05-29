# Name: Johan Tom Chacko
# Date: 2026-05-27
# What this file does: holds the three cities, Open-Meteo URL, db path, and poller settings.

import os
from dataclasses import dataclass

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/weather.db")

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
CURRENT_FIELDS = (
    "temperature_2m",
    "apparent_temperature",
    "precipitation",
    "wind_speed_10m",
    "weather_code",
)


@dataclass(frozen=True)
class City:
    name: str
    latitude: float
    longitude: float


# Coordinates from the assignment spec
CITIES = (
    City("Ottawa", 45.42, -75.69),
    City("Toronto", 43.70, -79.42),
    City("Vancouver", 49.25, -123.12),
)

# Poll more often than hourly; duplicates get filtered out when storing
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
ENABLE_POLLER = os.getenv("ENABLE_POLLER", "true").lower() == "true"
