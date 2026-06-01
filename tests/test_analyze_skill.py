# Name: Johan Tom Chacko
# Date: 2026-05-29
# What this file does: tests for the Cursor data_analysis analyze.py script.

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Event, Reading


def _write_sample_db(db_path: Path) -> None:
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    observed_at = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)

    with Session() as session:
        session.add(
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
        session.add(
            Event(
                city="Ottawa",
                observed_at=observed_at,
                event_type="temperature_shift",
                summary="Temperature rose 3.5C",
                reason="Threshold crossed",
            )
        )
        session.commit()


def _run_analyze(db_path: Path, *args: str) -> dict:
    script = Path(__file__).resolve().parents[1] / ".cursor" / "skills" / "data_analysis" / "analyze.py"
    result = subprocess.run(
        [sys.executable, str(script), "--db", str(db_path), *args],
        capture_output=True,
        text=True,
        check=True,
        cwd=Path(__file__).resolve().parents[1],
    )
    return json.loads(result.stdout)


def test_analyze_summary_on_empty_db(tmp_path):
    db_path = tmp_path / "empty.db"

    data = _run_analyze(db_path, "summary")

    assert data["readings_total"] == 0
    assert data["events_total"] == 0
    assert data["readings_by_city"] == {}
    assert data["events_by_city"] == {}


def test_analyze_summary_with_stored_data(tmp_path):
    db_path = tmp_path / "weather.db"
    _write_sample_db(db_path)

    data = _run_analyze(db_path, "summary")

    assert data["readings_total"] == 1
    assert data["events_total"] == 1
    assert data["readings_by_city"]["Ottawa"] == 1
    assert data["events_by_city"]["Ottawa"] == 1


def test_analyze_events_by_type(tmp_path):
    db_path = tmp_path / "weather.db"
    _write_sample_db(db_path)

    data = _run_analyze(db_path, "events-by-type", "--city", "Ottawa")

    assert data["city_filter"] == "Ottawa"
    assert data["events_by_type"]["temperature_shift"] == 1
