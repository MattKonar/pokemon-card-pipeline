# Pokemon Card Pipeline

Batch data pipeline that ingests Pokemon card data from the Pokemon TCG API into PostgreSQL using a bronze/silver/gold warehouse layout.

Current implementation focuses on reliable **bronze ingestion** with:
- API key enforcement
- per-set ingestion (instead of one global full scan)
- resumable checkpoints by set/page
- retries with exponential backoff for transient API failures

## Architecture

Data flow:

`Pokemon TCG API -> bronze (raw + checkpoints) -> silver -> gold`

Implemented now:
- `bronze.pokemon_cards_raw` upserted by `card_id`
- `bronze.ingestion_set_checkpoints` to resume failed runs

Defined (schema/contracts present, transforms not yet implemented in code):
- `silver.pokemon_cards`
- `gold.set_summary`

## Repository Layout

```text
docker/      Docker Compose for Postgres
sql/         Schema and migration SQL
src/         Python pipeline code
docs/        Project docs and contracts
```

## Prerequisites

- Python 3.11+ (venv recommended)
- Docker Desktop

## Setup

1. From repo root, start Postgres:

```bash
docker compose -f docker/docker-compose.yml up -d
```

2. Create and activate virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Create `.env` with required key:

```dotenv
POKEMON_TCG_API_KEY=your_api_key_here
```

Optional DB vars (defaults shown):

```dotenv
POSTGRES_USER=pokemon
POSTGRES_PASSWORD=pokemon
POSTGRES_DB=pokemon
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

## Run

Run from repo root:

```bash
python -m src.main
```

Important: use module mode (`python -m src.main`), not `python src/main.py`.

## Recommended Runtime Settings

For better stability against transient API `504`/timeout responses:

```bash
PAGE_SIZE=50 \
SETS_PAGE_SIZE=250 \
HTTP_READ_TIMEOUT_SECONDS=120 \
HTTP_PAGE_MAX_ATTEMPTS=12 \
HTTP_PAGE_BACKOFF_SECONDS=2 \
HTTP_PAGE_MAX_BACKOFF_SECONDS=90 \
SLEEP_SECONDS=0.2 \
python -m src.main
```

## Resume / Checkpoint Behavior

The pipeline writes progress to `bronze.ingestion_set_checkpoints`:
- one row per `(source, set_id)`
- stores `next_page`, `completed`, and `last_error`

On rerun, it:
- skips completed sets
- resumes incomplete sets from `next_page`
- continues past transient failures unless configured otherwise

Useful control variables:
- `ONLY_SET_IDS=sv1,sv2` process only listed sets
- `MAX_SETS=10` limit number of sets in a run
- `REPROCESS_COMPLETED=true` force full reprocess of completed sets
- `STOP_ON_SET_ERROR=true` fail immediately on first set failure
- `FAIL_ON_ANY_FAILURE=true` finish run then exit non-zero if any set failed
- `CARD_SELECT_FIELDS=id,name,set.id,set.name` request a reduced payload

## HTTP Retry/Timeout Controls

- `HTTP_CONNECT_TIMEOUT_SECONDS` (default: `5`)
- `HTTP_READ_TIMEOUT_SECONDS` (default: `60`)
- `HTTP_PAGE_MAX_ATTEMPTS` (default: `10`)
- `HTTP_PAGE_BACKOFF_SECONDS` (default: `1`)
- `HTTP_PAGE_MAX_BACKOFF_SECONDS` (default: `60`)
- `HTTP_PAGE_JITTER_SECONDS` (default: `0.5`)

## Existing Database Migration

If your local DB was created before the current bronze schema change, run:

```bash
docker exec -i pokemon_postgres psql -U pokemon -d pokemon < sql/02_migrate_bronze_schema.sql
```

If you prefer a clean reset:

```bash
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up -d
```

## Quick Checks

View checkpoint status:

```sql
SELECT source, set_id, next_page, completed, last_error, updated_at
FROM bronze.ingestion_set_checkpoints
ORDER BY completed, updated_at DESC;
```

View bronze row count:

```sql
SELECT COUNT(*) FROM bronze.pokemon_cards_raw;
```

## Troubleshooting

- `ModuleNotFoundError: No module named 'src'`
  - Run `python -m src.main` from repo root.
- `RuntimeError: POKEMON_TCG_API_KEY is required`
  - Add key to `.env` or export env var before running.
- Intermittent `504`/timeouts
  - Lower `PAGE_SIZE`, increase retry/backoff vars, and rerun; checkpointing will resume progress.
