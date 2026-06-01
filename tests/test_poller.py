# Name: Johan Tom Chacko
# Date: 2026-05-28
# What this file does: poller tests with a fake Open-Meteo response (no real network calls).

import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import httpx

from app import poller
from app.db.repository import count_events, count_readings
from app.poller import _to_utc, poll_all_cities, poll_city


def _api_payload(
    time_value: str = "2026-05-27T12:00",
    *,
    temperature: float = 18.0,
) -> dict:
    return {
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


def _mock_response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    return response


def test_poll_city_stores_reading_from_api(db):
    client = MagicMock()
    client.get.return_value = _mock_response(_api_payload())

    poll_city(db, client, "Ottawa", 45.42, -75.69)

    assert count_readings(db) == 1
    client.get.assert_called_once()


def test_poll_city_skips_duplicate_reading(db):
    client = MagicMock()
    client.get.return_value = _mock_response(_api_payload())

    poll_city(db, client, "Ottawa", 45.42, -75.69)
    poll_city(db, client, "Ottawa", 45.42, -75.69)

    assert count_readings(db) == 1
    assert client.get.call_count == 2


def test_poll_city_handles_http_error(db):
    client = MagicMock()
    client.get.side_effect = httpx.HTTPError("service unavailable")

    poll_city(db, client, "Ottawa", 45.42, -75.69)

    assert count_readings(db) == 0


def test_poll_city_creates_event_after_temperature_shift(db):
    client = MagicMock()
    client.get.side_effect = [
        _mock_response(_api_payload("2026-05-27T11:00", temperature=15.0)),
        _mock_response(_api_payload("2026-05-27T12:00", temperature=19.0)),
    ]

    poll_city(db, client, "Ottawa", 45.42, -75.69)
    poll_city(db, client, "Ottawa", 45.42, -75.69)

    assert count_readings(db) == 2
    assert count_events(db) == 1


def test_poll_city_skips_event_detection_on_duplicate(db):
    client = MagicMock()
    client.get.return_value = _mock_response(_api_payload())

    poll_city(db, client, "Ottawa", 45.42, -75.69)
    poll_city(db, client, "Ottawa", 45.42, -75.69)

    assert count_readings(db) == 1
    assert count_events(db) == 0


def test_poll_all_cities_stores_one_reading_per_city(db):
    with patch("app.poller.httpx.Client") as client_cls:
        client = MagicMock()
        client.__enter__.return_value = client
        client.get.return_value = _mock_response(_api_payload())
        client_cls.return_value = client

        poll_all_cities()

    assert count_readings(db) == 3


def test_to_utc_converts_toronto_local_time():
    observed_at = _to_utc("2026-05-27T12:00", "America/Toronto")

    assert observed_at.tzinfo == timezone.utc
    assert observed_at == datetime(2026, 5, 27, 16, 0, tzinfo=timezone.utc)


def test_poller_loop_survives_poll_cycle_error():
    async def run() -> None:
        sleep_calls = 0

        async def stop_after_first_sleep(_seconds: float) -> None:
            nonlocal sleep_calls
            sleep_calls += 1
            raise asyncio.CancelledError()

        with patch.object(poller, "poll_all_cities", side_effect=RuntimeError("boom")), patch.object(
            asyncio, "sleep", side_effect=stop_after_first_sleep
        ):
            try:
                await poller.poller_loop()
            except asyncio.CancelledError:
                pass

        assert sleep_calls == 1

    asyncio.run(run())
