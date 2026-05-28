from datetime import datetime, timezone

from app.db.models import Event, Reading


def parse_observed_at(value: str) -> datetime:
    observed_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=timezone.utc)
    return observed_at


def add_reading(db, *, city: str, observed_at: datetime, weather_code: int = 3) -> Reading:
    reading = Reading(
        city=city,
        observed_at=observed_at,
        temperature_2m=18.0,
        apparent_temperature=17.0,
        precipitation=0.0,
        wind_speed_10m=12.0,
        weather_code=weather_code,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def add_event(db, *, city: str, observed_at: datetime, event_type: str = "temperature_shift") -> Event:
    event = Event(
        city=city,
        observed_at=observed_at,
        event_type=event_type,
        summary="Temperature rose 3.5°C",
        reason="Exceeded threshold",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def test_readings_empty(client):
    response = client.get("/readings")

    assert response.status_code == 200
    assert response.json() == []


def test_readings_response_shape(client, db):
    observed_at = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    reading = add_reading(db, city="Ottawa", observed_at=observed_at)

    response = client.get("/readings")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
    assert set(data[0].keys()) == {
        "id",
        "city",
        "observed_at",
        "temperature_2m",
        "apparent_temperature",
        "precipitation",
        "wind_speed_10m",
        "weather_code",
    }
    assert data[0]["id"] == reading.id
    assert data[0]["city"] == "Ottawa"
    assert parse_observed_at(data[0]["observed_at"]) == observed_at
    assert data[0]["temperature_2m"] == 18.0
    assert data[0]["weather_code"] == 3


def test_readings_city_filter(client, db):
    observed_at = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    add_reading(db, city="Ottawa", observed_at=observed_at)
    add_reading(db, city="Toronto", observed_at=observed_at)

    response = client.get("/readings?city=Ottawa")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["city"] == "Ottawa"


def test_readings_limit(client, db):
    base = datetime(2026, 5, 27, 10, 0, tzinfo=timezone.utc)
    for hour in range(3):
        add_reading(
            db,
            city="Ottawa",
            observed_at=base.replace(hour=10 + hour),
        )

    response = client.get("/readings?city=Ottawa&limit=2")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_readings_order_newest_first(client, db):
    earlier = datetime(2026, 5, 27, 10, 0, tzinfo=timezone.utc)
    later = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    add_reading(db, city="Ottawa", observed_at=earlier)
    add_reading(db, city="Ottawa", observed_at=later)

    response = client.get("/readings?city=Ottawa")

    assert response.status_code == 200
    observed_times = [parse_observed_at(item["observed_at"]) for item in response.json()]
    assert observed_times == [later, earlier]


def test_events_empty(client):
    response = client.get("/events")

    assert response.status_code == 200
    assert response.json() == []


def test_events_response_shape(client, db):
    observed_at = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    event = add_event(db, city="Toronto", observed_at=observed_at)

    response = client.get("/events")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
    assert set(data[0].keys()) == {
        "id",
        "city",
        "observed_at",
        "event_type",
        "summary",
        "reason",
    }
    assert data[0]["id"] == event.id
    assert data[0]["city"] == "Toronto"
    assert parse_observed_at(data[0]["observed_at"]) == observed_at
    assert data[0]["event_type"] == "temperature_shift"
    assert data[0]["summary"] == "Temperature rose 3.5°C"
    assert data[0]["reason"] == "Exceeded threshold"


def test_events_city_filter(client, db):
    observed_at = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    add_event(db, city="Toronto", observed_at=observed_at)
    add_event(db, city="Vancouver", observed_at=observed_at)

    response = client.get("/events?city=Toronto")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["city"] == "Toronto"


def test_events_limit(client, db):
    base = datetime(2026, 5, 27, 10, 0, tzinfo=timezone.utc)
    for hour in range(3):
        add_event(
            db,
            city="Toronto",
            observed_at=base.replace(hour=10 + hour),
        )

    response = client.get("/events?city=Toronto&limit=1")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_events_order_newest_first(client, db):
    earlier = datetime(2026, 5, 27, 10, 0, tzinfo=timezone.utc)
    later = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    add_event(db, city="Toronto", observed_at=earlier)
    add_event(db, city="Toronto", observed_at=later)

    response = client.get("/events?city=Toronto")

    assert response.status_code == 200
    observed_times = [parse_observed_at(item["observed_at"]) for item in response.json()]
    assert observed_times == [later, earlier]
