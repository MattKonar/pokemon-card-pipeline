# Data Contracts

This document defines the target tables for v1.
Contracts come before code so we can build the pipeline against a clear target shape.

## Bronze layer

### bronze_pokemon_cards_raw
Purpose
Store raw API responses for traceability and replay.

Grain
One row per card id per ingestion run.

Keys
Unique: ingestion_run_id, card_id

Columns
- ingestion_run_id (text) unique identifier for a pipeline run
- ingested_at (timestamp) when the record was ingested
- source (text) which endpoint produced the record
- card_id (text) card identifier from the API
- raw_json (jsonb) raw payload for the card

## Silver layer

### silver_pokemon_cards
Purpose
Clean and type a stable set of fields for analysis.

Grain
One row per card id.

Primary key
- card_id

Columns
- card_id (text)
- name (text)
- supertype (text)
- subtype (text, nullable)
- hp (integer, nullable)
- rarity (text, nullable)
- set_id (text)
- set_name (text)
- set_series (text, nullable)
- set_release_date (date, nullable)

## Gold layer

### gold_set_summary
Purpose
Reporting table summarizing cards by set.

Grain
One row per set.

Primary key
- set_id

Columns
- set_id (text)
- set_name (text)
- total_cards (integer)
- avg_hp (numeric, nullable)
- rare_count (integer)

## Notes
- The first implementation can start with a smaller subset of columns.
- This contract is the target shape for v1.
- The pipeline must be rerunnable without creating duplicates.
