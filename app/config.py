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


CITIES = (
    City("Ottawa", 45.42, -75.69),
    City("Toronto", 43.70, -79.42),
    City("Vancouver", 49.25, -123.12),
)
