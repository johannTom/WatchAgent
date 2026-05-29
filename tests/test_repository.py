# Name: Johan Tom Chacko
# Date: 2026-05-27
# What this file does: checks count_readings and count_events on an empty db.

from app.db.repository import count_events, count_readings


def test_count_helpers_empty_db(db):
    assert count_readings(db) == 0
    assert count_events(db) == 0
