---
name: watchagent-data-analysis
description: Query WatchAgent SQLite readings and events for trends, per-city summaries, and event breakdowns. Use when analyzing stored weather data or answering questions about collected readings and events.
---

# WatchAgent data analysis

Executable skill script: `.cursor/skills/data_analysis/analyze.py`

## Prerequisites

Repository root, dependencies installed (`pip install -r requirements.txt`). App or Docker should have run long enough to collect data (empty DB returns zero counts).

## Commands

```bash
python .cursor/skills/data_analysis/analyze.py summary
python .cursor/skills/data_analysis/analyze.py events-by-type --city Ottawa
python .cursor/skills/data_analysis/analyze.py recent-events --limit 10
python .cursor/skills/data_analysis/analyze.py temperature-trend --city Toronto --limit 20
```

## Environment

- `DATABASE_URL` — default `sqlite:///./data/weather.db` (same as app)
- `--db path/to/weather.db` — override SQLite path

## Output

JSON to stdout. Use `summary` first, then `events-by-type` or `temperature-trend` as needed. Event rules: `app/events.py` and README Event detection section.
