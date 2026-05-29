# Name: Johan Tom Chacko
# Date: 2026-05-29
# What this file does: checks that file-based sqlite still has data after reopening (like Docker ./data).

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Event, Reading
from app.db.repository import count_events, count_readings, list_readings, store_reading_if_new


def _file_session_factory(db_path: Path):
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_file_database_persists_readings_across_connections(tmp_path):
    db_path = tmp_path / "weather.db"
    session_factory = _file_session_factory(db_path)
    observed_at = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)

    write_session = session_factory()
    store_reading_if_new(
        write_session,
        city="Ottawa",
        observed_at=observed_at,
        temperature_2m=18.0,
        apparent_temperature=17.0,
        precipitation=0.0,
        wind_speed_10m=12.0,
        weather_code=3,
    )
    write_session.close()

    read_session = session_factory()
    readings = list_readings(read_session, city="Ottawa")
    read_session.close()

    assert len(readings) == 1
    assert readings[0].city == "Ottawa"
    assert db_path.exists()


def test_file_database_persists_events_across_connections(tmp_path):
    db_path = tmp_path / "weather.db"
    session_factory = _file_session_factory(db_path)
    observed_at = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)

    write_session = session_factory()
    write_session.add(
        Event(
            city="Toronto",
            observed_at=observed_at,
            event_type="temperature_shift",
            summary="Temperature rose 3.5°C",
            reason="Exceeded threshold",
        )
    )
    write_session.commit()
    write_session.close()

    read_session = session_factory()
    assert count_events(read_session) == 1
    read_session.close()
    assert db_path.stat().st_size > 0


def test_new_file_database_starts_empty(tmp_path):
    db_path = tmp_path / "weather.db"
    session_factory = _file_session_factory(db_path)

    session = session_factory()
    assert count_readings(session) == 0
    assert count_events(session) == 0
    session.close()
