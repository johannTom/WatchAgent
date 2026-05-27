from datetime import datetime, timezone

from app.db.models import Event, Reading


def test_health_empty_db(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "readings_stored": 0,
        "events_stored": 0,
    }


def test_health_seeded_db(client, db):
    observed_at = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)

    db.add(
        Reading(
            city="Ottawa",
            observed_at=observed_at,
            temperature_2m=18.0,
            apparent_temperature=17.0,
            precipitation=0.0,
            wind_speed_10m=12.0,
            weather_code=3,
        )
    )
    db.add(
        Event(
            city="Ottawa",
            observed_at=observed_at,
            event_type="temperature_shift",
            summary="Temperature rose 3.5°C",
            reason="Exceeded threshold",
        )
    )
    db.commit()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "readings_stored": 1,
        "events_stored": 1,
    }
