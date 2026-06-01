# Name: Johan Tom Chacko
# Date: 2026-05-29
# What this file does: end-to-end tests from mocked poll through API responses.

from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.db.repository import count_events, count_readings, store_reading_if_new
from app.events import evaluate_reading
from app.poller import poll_city


def _mock_response(time_value: str, temperature: float) -> MagicMock:
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "timezone": "America/Toronto",
        "current": {
            "time": time_value,
            "temperature_2m": temperature,
            "apparent_temperature": temperature - 1.0,
            "precipitation": 0.0,
            "wind_speed_10m": 12.0,
            "weather_code": 3,
        },
    }
    return response


def test_poll_to_api_pipeline(client, db):
    client_mock = MagicMock()
    client_mock.get.side_effect = [
        _mock_response("2026-05-27T11:00", 15.0),
        _mock_response("2026-05-27T12:00", 19.0),
    ]

    poll_city(db, client_mock, "Ottawa", 45.42, -75.69)
    poll_city(db, client_mock, "Ottawa", 45.42, -75.69)

    assert count_readings(db) == 2
    assert count_events(db) == 1

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {
        "status": "ok",
        "readings_stored": 2,
        "events_stored": 1,
    }

    readings = client.get("/readings?city=Ottawa")
    assert readings.status_code == 200
    assert len(readings.json()["readings"]) == 2

    events = client.get("/events?city=Ottawa")
    payload = events.json()["events"]
    assert len(payload) == 1
    assert payload[0]["event_type"] == "temperature_shift"
    assert payload[0]["city"] == "Ottawa"
    assert payload[0]["summary"]
    assert payload[0]["reason"]


def test_duplicate_poll_does_not_create_duplicate_events(db):
    observed_at = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    previous = store_reading_if_new(
        db,
        city="Ottawa",
        observed_at=datetime(2026, 5, 27, 11, 0, tzinfo=timezone.utc),
        temperature_2m=15.0,
        apparent_temperature=14.0,
        precipitation=0.0,
        wind_speed_10m=10.0,
        weather_code=3,
    )
    assert previous is not None

    current = store_reading_if_new(
        db,
        city="Ottawa",
        observed_at=observed_at,
        temperature_2m=19.0,
        apparent_temperature=18.0,
        precipitation=0.0,
        wind_speed_10m=10.0,
        weather_code=3,
    )
    evaluate_reading(db, current)
    assert count_events(db) == 1

    duplicate = store_reading_if_new(
        db,
        city="Ottawa",
        observed_at=observed_at,
        temperature_2m=19.0,
        apparent_temperature=18.0,
        precipitation=0.0,
        wind_speed_10m=10.0,
        weather_code=3,
    )
    assert duplicate is None
    assert count_events(db) == 1
