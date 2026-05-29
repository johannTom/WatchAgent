#!/usr/bin/env python3
# Name: Johan Tom Chacko
# Date: 2026-05-29
# What this file does: Cursor skill script — query my weather db and print JSON summaries.

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from app.db.models import Base, Event, Reading  # noqa: E402


def _default_database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./data/weather.db")


def _engine(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


def _ensure_schema(engine) -> None:
    if str(engine.url).startswith("sqlite"):
        db_path = Path(str(engine.url.database or ""))
        if db_path.parent != Path("."):
            db_path.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.isoformat()


def cmd_summary(session) -> dict:
    reading_count = session.scalar(select(func.count()).select_from(Reading)) or 0
    event_count = session.scalar(select(func.count()).select_from(Event)) or 0

    by_city = session.execute(
        select(Reading.city, func.count()).group_by(Reading.city).order_by(Reading.city)
    ).all()
    events_by_city = session.execute(
        select(Event.city, func.count()).group_by(Event.city).order_by(Event.city)
    ).all()

    return {
        "readings_total": reading_count,
        "events_total": event_count,
        "readings_by_city": {city: count for city, count in by_city},
        "events_by_city": {city: count for city, count in events_by_city},
    }


def cmd_events_by_type(session, city: str | None) -> dict:
    query = select(Event.event_type, func.count()).group_by(Event.event_type)
    if city:
        query = query.where(Event.city == city)
    rows = session.execute(query.order_by(Event.event_type)).all()
    return {
        "city_filter": city,
        "events_by_type": {event_type: count for event_type, count in rows},
    }


def cmd_recent_events(session, limit: int, city: str | None) -> dict:
    query = select(Event).order_by(Event.observed_at.desc()).limit(limit)
    if city:
        query = query.where(Event.city == city)
    events = session.scalars(query).all()
    return {
        "city_filter": city,
        "limit": limit,
        "events": [
            {
                "city": event.city,
                "observed_at": _iso(event.observed_at),
                "event_type": event.event_type,
                "summary": event.summary,
                "reason": event.reason,
            }
            for event in events
        ],
    }


def cmd_temperature_trend(session, city: str, limit: int) -> dict:
    readings = session.scalars(
        select(Reading)
        .where(Reading.city == city)
        .order_by(Reading.observed_at.desc())
        .limit(limit)
    ).all()
    temps = [reading.temperature_2m for reading in readings]
    return {
        "city": city,
        "limit": limit,
        "readings": [
            {
                "observed_at": _iso(reading.observed_at),
                "temperature_2m": reading.temperature_2m,
                "weather_code": reading.weather_code,
            }
            for reading in readings
        ],
        "stats": {
            "count": len(temps),
            "min_c": min(temps) if temps else None,
            "max_c": max(temps) if temps else None,
            "latest_c": temps[0] if temps else None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze WatchAgent SQLite data")
    parser.add_argument(
        "--db",
        help="SQLite file path (overrides DATABASE_URL)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("summary", help="Counts by city")

    events_type = sub.add_parser("events-by-type", help="Event counts grouped by type")
    events_type.add_argument("--city")

    recent = sub.add_parser("recent-events", help="Most recent events")
    recent.add_argument("--limit", type=int, default=10)
    recent.add_argument("--city")

    trend = sub.add_parser("temperature-trend", help="Recent temperatures for one city")
    trend.add_argument("--city", required=True)
    trend.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()

    if args.db:
        database_url = f"sqlite:///{Path(args.db).resolve()}"
    else:
        database_url = _default_database_url()

    engine = _engine(database_url)
    _ensure_schema(engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        if args.command == "summary":
            result = cmd_summary(session)
        elif args.command == "events-by-type":
            result = cmd_events_by_type(session, args.city)
        elif args.command == "recent-events":
            result = cmd_recent_events(session, args.limit, args.city)
        elif args.command == "temperature-trend":
            result = cmd_temperature_trend(session, args.city, args.limit)
        else:
            parser.error(f"unknown command: {args.command}")
            return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
