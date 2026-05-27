from datetime import datetime, timezone

from app.db.repository import count_readings, store_reading_if_new


def _reading_payload(observed_at: datetime, city: str = "Ottawa") -> dict:
    return {
        "city": city,
        "observed_at": observed_at,
        "temperature_2m": 18.5,
        "apparent_temperature": 17.0,
        "precipitation": 0.0,
        "wind_speed_10m": 12.0,
        "weather_code": 3,
    }


def test_duplicate_timestamp_is_not_stored_twice(db):
    observed_at = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    payload = _reading_payload(observed_at)

    first = store_reading_if_new(db, **payload)
    second = store_reading_if_new(db, **payload)

    assert first is not None
    assert second is None
    assert count_readings(db) == 1


def test_same_timestamp_different_cities_are_both_stored(db):
    observed_at = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)

    ottawa = store_reading_if_new(db, **_reading_payload(observed_at, "Ottawa"))
    toronto = store_reading_if_new(db, **_reading_payload(observed_at, "Toronto"))

    assert ottawa is not None
    assert toronto is not None
    assert count_readings(db) == 2


def test_same_city_different_timestamps_are_both_stored(db):
    first = store_reading_if_new(
        db,
        **_reading_payload(datetime(2026, 5, 27, 11, 0, tzinfo=timezone.utc)),
    )
    second = store_reading_if_new(
        db,
        **_reading_payload(datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)),
    )

    assert first is not None
    assert second is not None
    assert count_readings(db) == 2
