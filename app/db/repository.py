from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Event, Reading


def count_readings(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Reading)) or 0


def count_events(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Event)) or 0
