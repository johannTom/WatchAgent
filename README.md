# WatchAgent: Weather Monitor & AI Assistant

Nokia take-home — weather monitor backend plus Cursor AI Assistant setup.

Polls Ottawa, Toronto, and Vancouver via Open-Meteo, stores readings in SQLite, detects notable events, and exposes `/health`, `/readings`, and `/events`. The `.cursor/` folder holds rules, agents, and a data-analysis skill for the AI Assistant section.

**Systems Analysis and Design report:** [docs/system-analysis-and-design.md](docs/system-analysis-and-design.md) (SENG71000-style use cases, diagrams, technology stack)

## Overview

Single FastAPI process with a background poller:

1. **Poll** — fetch current conditions from Open-Meteo every 300s (configurable) for all three cities
2. **Store** — insert readings once; skip duplicates by `(city, observed_at)`
3. **Detect** — compare each new reading to the previous one for that city; store events with what / where / when / why
4. **Serve** — API reads from SQLite only; clients do not access the database directly

No frontend required.

### Monitored cities

| City | Latitude | Longitude |
|---|---|---|
| Ottawa | 45.42 | -75.69 |
| Toronto | 43.70 | -79.42 |
| Vancouver | 49.25 | -123.12 |

Polling runs every 300s (more frequently than Open-Meteo’s hourly updates). Duplicate `(city, observed_at)` pairs are skipped on insert.

### Stored reading fields (Open-Meteo)

Each poll stores these five current-condition fields per city:

- `temperature_2m`
- `apparent_temperature`
- `precipitation`
- `wind_speed_10m`
- `weather_code`

## Architecture

![WatchAgent architecture](docs/architecture-diagram.svg)

The diagram has two zones:

- **Runtime (top)** — Open-Meteo → poller → SQLite ← event detection; FastAPI queries SQLite; client calls the API
- **AI Assistant (bottom)** — `.cursor/` rules, agents, and `analyze.py`; read-only access to SQLite; not started by Docker

| Component | Role |
|---|---|
| **Open-Meteo** | External weather API (no key) |
| **Poller** | Fetch → dedupe → persist → event detection |
| **SQLite** | Readings and events; `./data/` volume in Docker |
| **Event detection** | Change-based rules on consecutive readings per city |
| **FastAPI** | `/health`, `/readings`, `/events`; poller on app lifespan |
| **`.cursor/`** | Cursor rules, agents, data analysis skill |

Also in `docs/`: [system-analysis-and-design.md](docs/system-analysis-and-design.md) (full SAD report), [use-case-diagram.svg](docs/use-case-diagram.svg), [class-diagram.svg](docs/class-diagram.svg), [sequence-diagram.svg](docs/sequence-diagram.svg).

## Technology choices

| Choice | Why |
|---|---|
| **Python 3.11** | Assignment stack; used in Dockerfile |
| **FastAPI + Uvicorn** | REST API and OpenAPI docs |
| **SQLAlchemy 2** | ORM for readings/events |
| **SQLite** | Single-file DB; Docker volume mount |
| **httpx** | Open-Meteo HTTP client in poller |
| **pytest** | 56 tests (dedup, events, API, integration, system, analyze skill) |
| **Docker Compose** | One-command run for reviewers |

Open-Meteo: free, no credentials; see [Stored reading fields](#stored-reading-fields-open-meteo) above.

## CI

GitHub Actions runs on every push to `main` (see `.github/workflows/ci.yml`):

1. **test** — `pytest -q` with in-memory SQLite (`ENABLE_POLLER=false`)
2. **build** — `docker build -t watchagent .`

## Run with Docker

Requirements: Docker and Git.

```bash
git clone https://github.com/johannTom/WatchAgent.git
cd WatchAgent
cp .env.example .env
docker compose up --build
```

API: `http://localhost:8000`. Poller starts automatically. SQLite persists in `./data/` on the host.

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/weather.db` | SQLite database path |
| `POLL_INTERVAL_SECONDS` | `300` | Seconds between poll cycles |
| `ENABLE_POLLER` | `true` | Start background poller on boot |

## API

| Endpoint | Query params | Description |
|---|---|---|
| `GET /health` | — | Service status and stored row counts |
| `GET /readings` | `city`, `limit` | `{ "readings": [ ... ] }` newest first |
| `GET /events` | `city`, `limit` | `{ "events": [ ... ] }` newest first |

`city` optional. `limit` defaults to 50 (max 500).

```bash
curl "http://localhost:8000/readings?city=Ottawa&limit=10"
curl "http://localhost:8000/events?city=Toronto&limit=10"
```

### Example responses

`GET /readings` returns:

```json
{
  "readings": [
    {
      "id": 1,
      "city": "Ottawa",
      "observed_at": "2026-05-27T18:00:00+00:00",
      "temperature_2m": 22.5,
      "apparent_temperature": 21.0,
      "precipitation": 0.0,
      "wind_speed_10m": 12.0,
      "weather_code": 2
    }
  ]
}
```

`GET /events` returns:

```json
{
  "events": [
    {
      "id": 1,
      "city": "Toronto",
      "observed_at": "2026-05-27T18:00:00+00:00",
      "event_type": "temperature_shift",
      "summary": "Temperature rose 3.2°C to 18.5°C",
      "reason": "3.2°C change since last reading (threshold 3°C)"
    }
  ]
}
```

Interactive docs: `http://localhost:8000/docs`

## Event detection

Events compare each new reading to the previous one for the same city. Fixed thresholds (e.g. temperature > 30°C) are avoided in favour of change-based, city-aware rules.

Each event includes **what** (`summary`), **where** (`city`), **when** (`observed_at`), and **why** (`reason`).

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

`condition_change` fires only when the category changes between consecutive readings.

### Rules

- **temperature_shift** — change of at least 3°C since the previous reading
- **precipitation_started** — precipitation crosses from below 0.5 mm to at least 0.5 mm
- **strong_wind** — wind crosses city threshold (Vancouver 35 km/h; Ottawa/Toronto 45 km/h)
- **condition_change** — WMO category boundary crossed

First reading per city produces no events (nothing to compare).

## Local development (without Docker)

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
pytest -q
```

## Cursor setup (AI Assistant)

Project-specific Cursor configuration in `.cursor/`. Separate from the runtime API — used for development, review, and analyzing stored data in Cursor.

### Rules (`.cursor/rules/`)

| Rule | Scope | Purpose |
|---|---|---|
| `project-conventions.mdc` | Always | Architecture, dedup, UTC timestamps, test env |
| `event-design.mdc` | `app/events.py`, event tests | Change-based rules, WMO categories |
| `poller-resilience.mdc` | `app/poller.py`, poller tests | Fetch failures, loop survival, insert-only-on-new |

### Agents (`.cursor/agents/`)

| Agent | Use when |
|---|---|
| `event-reviewer` | Changing event detection or thresholds |
| `api-storage-reviewer` | Changing models, repository, or API routes |

### Skill: data analysis (`.cursor/skills/data_analysis/`)

```bash
python .cursor/skills/data_analysis/analyze.py summary
python .cursor/skills/data_analysis/analyze.py events-by-type --city Ottawa
python .cursor/skills/data_analysis/analyze.py recent-events --limit 5
python .cursor/skills/data_analysis/analyze.py temperature-trend --city Toronto --limit 10
```

Uses `DATABASE_URL` (default `./data/weather.db`). Creates schema if needed; returns empty JSON counts on an empty DB. See `SKILL.md` in that folder.

## Project structure

```
app/                FastAPI, poller, events, DB layer
tests/              pytest (dedup, events, API, integration)
docs/               SAD report, architecture, use case, class, sequence diagrams
.cursor/            Rules, agents, data analysis skill
Dockerfile          Container image
docker-compose.yml  Local stack, volume-mounted SQLite
.env.example        Environment variables
requirements.txt    Dependencies
```
