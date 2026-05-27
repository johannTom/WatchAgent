from app.db.repository import count_events, count_readings


def test_count_helpers_empty_db(db):
    assert count_readings(db) == 0
    assert count_events(db) == 0
