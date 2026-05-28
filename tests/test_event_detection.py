from datetime import datetime, timezone

from app.db.models import Reading
from app.db.repository import count_events, store_reading_if_new
from app.events import detect_events, evaluate_reading


def _reading(**kwargs) -> Reading:
    defaults = {
        "id": 1,
        "city": "Ottawa",
        "apparent_temperature": 18.0,
        "precipitation": 0.0,
        "wind_speed_10m": 10.0,
        "weather_code": 3,
        "temperature_2m": 15.0,
    }
    defaults.update(kwargs)
    return Reading(**defaults)


def test_first_reading_produces_no_events():
    reading = _reading(observed_at=datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc))

    assert detect_events(reading, None) == []


def test_temperature_shift_is_detected():
    previous = _reading(
        observed_at=datetime(2026, 5, 27, 11, 0, tzinfo=timezone.utc),
        temperature_2m=15.0,
    )
    current = _reading(
        observed_at=datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc),
        temperature_2m=19.0,
    )

    event_types = [event[0] for event in detect_events(current, previous)]

    assert "temperature_shift" in event_types


def test_small_temperature_change_is_ignored():
    previous = _reading(
        observed_at=datetime(2026, 5, 27, 11, 0, tzinfo=timezone.utc),
        temperature_2m=15.0,
    )
    current = _reading(
        observed_at=datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc),
        temperature_2m=16.5,
    )

    assert detect_events(current, previous) == []


def test_precipitation_started_is_detected():
    previous = _reading(
        observed_at=datetime(2026, 5, 27, 11, 0, tzinfo=timezone.utc),
        precipitation=0.0,
    )
    current = _reading(
        observed_at=datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc),
        precipitation=1.0,
    )

    event_types = [event[0] for event in detect_events(current, previous)]

    assert "precipitation_started" in event_types


def test_strong_wind_is_detected():
    previous = _reading(
        observed_at=datetime(2026, 5, 27, 11, 0, tzinfo=timezone.utc),
        wind_speed_10m=40.0,
    )
    current = _reading(
        observed_at=datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc),
        wind_speed_10m=46.0,
    )

    event_types = [event[0] for event in detect_events(current, previous)]

    assert "strong_wind" in event_types


def test_same_weather_category_is_ignored():
    previous = _reading(
        observed_at=datetime(2026, 5, 27, 11, 0, tzinfo=timezone.utc),
        weather_code=1,
    )
    current = _reading(
        observed_at=datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc),
        weather_code=2,
    )

    assert detect_events(current, previous) == []


def test_condition_change_across_categories_is_detected():
    previous = _reading(
        observed_at=datetime(2026, 5, 27, 11, 0, tzinfo=timezone.utc),
        weather_code=3,
    )
    current = _reading(
        observed_at=datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc),
        weather_code=61,
    )

    event_types = [event[0] for event in detect_events(current, previous)]

    assert "condition_change" in event_types


def test_evaluate_reading_stores_event(db):
    previous_time = datetime(2026, 5, 27, 11, 0, tzinfo=timezone.utc)
    current_time = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)

    store_reading_if_new(
        db,
        city="Ottawa",
        observed_at=previous_time,
        temperature_2m=15.0,
        apparent_temperature=14.0,
        precipitation=0.0,
        wind_speed_10m=10.0,
        weather_code=3,
    )
    current = store_reading_if_new(
        db,
        city="Ottawa",
        observed_at=current_time,
        temperature_2m=19.0,
        apparent_temperature=18.0,
        precipitation=0.0,
        wind_speed_10m=10.0,
        weather_code=3,
    )

    evaluate_reading(db, current)

    assert count_events(db) == 1


def test_rain_code_change_within_category_is_ignored():
    previous = _reading(
        observed_at=datetime(2026, 5, 27, 11, 0, tzinfo=timezone.utc),
        weather_code=61,
    )
    current = _reading(
        observed_at=datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc),
        weather_code=63,
    )

    assert detect_events(current, previous) == []


def test_condition_change_to_thunderstorm_is_detected():
    previous = _reading(
        observed_at=datetime(2026, 5, 27, 11, 0, tzinfo=timezone.utc),
        weather_code=3,
    )
    current = _reading(
        observed_at=datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc),
        weather_code=95,
    )

    event_types = [event[0] for event in detect_events(current, previous)]

    assert "condition_change" in event_types


def test_vancouver_wind_threshold_is_lower_than_ottawa():
    previous = _reading(
        observed_at=datetime(2026, 5, 27, 11, 0, tzinfo=timezone.utc),
        wind_speed_10m=30.0,
    )
    vancouver = _reading(
        city="Vancouver",
        observed_at=datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc),
        wind_speed_10m=36.0,
    )
    ottawa = _reading(
        city="Ottawa",
        observed_at=datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc),
        wind_speed_10m=36.0,
    )

    vancouver_events = detect_events(vancouver, previous)
    ottawa_events = detect_events(ottawa, previous)

    assert any(event[0] == "strong_wind" for event in vancouver_events)
    assert ottawa_events == []
