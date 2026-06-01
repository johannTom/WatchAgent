# Name: Johan Tom Chacko
# Date: 2026-05-29
# What this file does: repository query and store helpers beyond empty counts.

from datetime import datetime, timezone

from app.db.repository import (
    count_events,
    count_readings,
    get_previous_reading,
    list_events,
    list_readings,
    store_event,
    store_reading_if_new,
)


def _reading_kwargs(observed_at: datetime, city: str = "Ottawa", temperature: float = 18.0) -> dict:
    return {
        "city": city,
        "observed_at": observed_at,
        "temperature_2m": temperature,
        "apparent_temperature": 17.0,
        "precipitation": 0.0,
        "wind_speed_10m": 12.0,
        "weather_code": 3,
    }


def test_count_helpers_empty_db(db):
    assert count_readings(db) == 0
    assert count_events(db) == 0


def test_get_previous_reading_returns_latest_before_timestamp(db):
    earlier = datetime(2026, 5, 27, 10, 0, tzinfo=timezone.utc)
    middle = datetime(2026, 5, 27, 11, 0, tzinfo=timezone.utc)
    latest = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)

    store_reading_if_new(db, **_reading_kwargs(earlier))
    store_reading_if_new(db, **_reading_kwargs(middle))
    store_reading_if_new(db, **_reading_kwargs(latest))

    previous = get_previous_reading(db, "Ottawa", latest)

    assert previous is not None
    assert previous.observed_at.replace(tzinfo=timezone.utc) == middle


def test_get_previous_reading_returns_none_for_first_reading(db):
    observed_at = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    store_reading_if_new(db, **_reading_kwargs(observed_at))

    assert get_previous_reading(db, "Ottawa", observed_at) is None


def test_list_readings_respects_limit(db):
    base = datetime(2026, 5, 27, 10, 0, tzinfo=timezone.utc)
    for hour in range(5):
        store_reading_if_new(db, **_reading_kwargs(base.replace(hour=10 + hour)))

    readings = list_readings(db, city="Ottawa", limit=2)

    assert len(readings) == 2


def test_list_events_city_filter(db):
    observed_at = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    store_event(
        db,
        city="Ottawa",
        observed_at=observed_at,
        event_type="temperature_shift",
        summary="Temperature rose",
        reason="3C change",
    )
    store_event(
        db,
        city="Toronto",
        observed_at=observed_at,
        event_type="temperature_shift",
        summary="Temperature rose",
        reason="3C change",
    )

    ottawa_events = list_events(db, city="Ottawa")

    assert len(ottawa_events) == 1
    assert ottawa_events[0].city == "Ottawa"


def test_store_event_persists_fields(db):
    observed_at = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    event = store_event(
        db,
        city="Vancouver",
        observed_at=observed_at,
        event_type="strong_wind",
        summary="Wind reached 40 km/h",
        reason="Crossed threshold",
    )

    assert event.id is not None
    assert event.city == "Vancouver"
    assert event.event_type == "strong_wind"
    assert count_events(db) == 1
