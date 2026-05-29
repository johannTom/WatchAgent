# WatchAgent: Weather Monitor & AI Assistant

Starter scaffold for the Nokia take-home project.

## Event detection

Notable events compare each new reading to the previous one for the same city. Fixed thresholds like "temperature > 30°C" are avoided in favour of change-based, city-aware rules.

### Condition categories

WMO weather codes are grouped so minor code changes within the same group do not create events:

| Category | WMO codes |
|---|---|
| clear | 0 |
| cloudy | 1, 2, 3 |
| fog | 45, 48 |
| drizzle/rain | 51–67, 80–82 |
| snow | 71–77, 85–86 |
| thunderstorm | 95–99 |

A `condition_change` event fires only when the category changes between consecutive readings (for example cloudy → drizzle/rain).

### Other rules

- **temperature_shift** — change of at least 3°C since the previous reading
- **precipitation_started** — hourly precipitation crosses from below 0.5 mm to at least 0.5 mm
- **strong_wind** — wind crosses a city threshold (Vancouver 35 km/h, Ottawa/Toronto 45 km/h)

## API

| Endpoint | Query params | Description |
|---|---|---|
| `GET /health` | — | Service status and stored row counts |
| `GET /readings` | `city`, `limit` | Latest weather readings (newest first) |
| `GET /events` | `city`, `limit` | Latest notable events (newest first) |

`city` is optional. `limit` defaults to 100 (max 500).

```bash
curl "http://localhost:8000/readings?city=Ottawa&limit=10"
curl "http://localhost:8000/events?city=Toronto&limit=10"
```

## Run with Docker

Requirements: Docker and Git.

```bash
git clone <your-repo>
cd watchagent-weather-monitor
cp .env.example .env
docker compose up --build
```

The API is available at `http://localhost:8000`. The poller starts automatically and SQLite data is stored in `./data/` on the host so it survives container restarts.

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/weather.db` | SQLite database path |
| `POLL_INTERVAL_SECONDS` | `300` | Seconds between poll cycles |
| `ENABLE_POLLER` | `true` | Start background poller on boot |

## Local development (without Docker)

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Run tests:

```bash
pytest -q
```

## Planned structure

- `app/` application code
- `tests/` automated tests
- `.cursor/` project-specific Cursor rules, agents, and skills
- `Dockerfile` container image definition
- `docker-compose.yml` local stack runner
- `.env.example` documented environment variables
- `requirements.txt` Python dependencies

This base structure is intentionally minimal so we can build the project step by step.
