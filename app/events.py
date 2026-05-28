from sqlalchemy.orm import Session

from app.db.models import Reading
from app.db.repository import get_previous_reading, store_event

TEMP_SHIFT_C = 3.0
PRECIP_START_MM = 0.5

WIND_THRESHOLDS_KMH = {
    "Ottawa": 45.0,
    "Toronto": 45.0,
    "Vancouver": 35.0,
}


def weather_category(code: int) -> str:
    if code == 0:
        return "clear"
    if code in (1, 2, 3):
        return "cloudy"
    if code in (45, 48):
        return "fog"
    if 51 <= code <= 67 or 80 <= code <= 82:
        return "drizzle/rain"
    if 71 <= code <= 77 or code in (85, 86):
        return "snow"
    if 95 <= code <= 99:
        return "thunderstorm"
    return "other"


def detect_events(reading: Reading, previous: Reading | None) -> list[tuple[str, str, str]]:
    if previous is None:
        return []

    events: list[tuple[str, str, str]] = []

    temp_delta = reading.temperature_2m - previous.temperature_2m
    if abs(temp_delta) >= TEMP_SHIFT_C:
        direction = "rose" if temp_delta > 0 else "fell"
        events.append(
            (
                "temperature_shift",
                f"Temperature {direction} {abs(temp_delta):.1f}°C to {reading.temperature_2m:.1f}°C",
                f"{abs(temp_delta):.1f}°C change since last reading (threshold {TEMP_SHIFT_C}°C)",
            )
        )

    if previous.precipitation < PRECIP_START_MM <= reading.precipitation:
        events.append(
            (
                "precipitation_started",
                f"Precipitation started ({reading.precipitation:.1f} mm/h)",
                f"Precipitation went from {previous.precipitation:.1f} to {reading.precipitation:.1f} mm",
            )
        )

    wind_threshold = WIND_THRESHOLDS_KMH.get(reading.city, 45.0)
    if previous.wind_speed_10m < wind_threshold <= reading.wind_speed_10m:
        events.append(
            (
                "strong_wind",
                f"Wind reached {reading.wind_speed_10m:.0f} km/h in {reading.city}",
                f"Crossed local threshold of {wind_threshold:.0f} km/h",
            )
        )

    previous_category = weather_category(previous.weather_code)
    current_category = weather_category(reading.weather_code)
    if previous_category != current_category:
        events.append(
            (
                "condition_change",
                f"Conditions changed from {previous_category} to {current_category}",
                (
                    f"Weather code {previous.weather_code} -> {reading.weather_code} "
                    f"crossed category boundary"
                ),
            )
        )

    return events


def evaluate_reading(db: Session, reading: Reading) -> list[tuple[str, str, str]]:
    previous = get_previous_reading(db, reading.city, reading.observed_at)
    detected = detect_events(reading, previous)

    for event_type, summary, reason in detected:
        store_event(
            db,
            city=reading.city,
            observed_at=reading.observed_at,
            event_type=event_type,
            summary=summary,
            reason=reason,
        )

    return detected
