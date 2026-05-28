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

## Planned structure

- `app/` application code
- `tests/` automated tests
- `.cursor/` project-specific Cursor rules, agents, and skills
- `Dockerfile` container image definition
- `docker-compose.yml` local stack runner
- `.env.example` documented environment variables
- `requirements.txt` Python dependencies

This base structure is intentionally minimal so we can build the project step by step.
