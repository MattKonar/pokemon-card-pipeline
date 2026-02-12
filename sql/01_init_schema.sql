CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

CREATE TABLE IF NOT EXISTS bronze.pokemon_cards_raw (
  ingestion_run_id TEXT NOT NULL,
  ingested_at TIMESTAMP NOT NULL DEFAULT NOW(),
  source TEXT NOT NULL,
  card_id TEXT NOT NULL,
  raw_json JSONB NOT NULL,
  PRIMARY KEY (ingestion_run_id, card_id)
);

CREATE TABLE IF NOT EXISTS silver.pokemon_cards (
  card_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  supertype TEXT NOT NULL,
  subtype TEXT,
  hp INTEGER,
  rarity TEXT,
  set_id TEXT NOT NULL,
  set_name TEXT NOT NULL,
  set_series TEXT,
  set_release_date DATE
);

CREATE TABLE IF NOT EXISTS gold.set_summary (
  set_id TEXT PRIMARY KEY,
  set_name TEXT NOT NULL,
  total_cards INTEGER NOT NULL,
  avg_hp NUMERIC,
  rare_count INTEGER NOT NULL
);