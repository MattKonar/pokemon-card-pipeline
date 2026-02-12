CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

CREATE TABLE IF NOT EXISTS bronze.pokemon_cards_raw (
  card_id TEXT PRIMARY KEY,
  last_ingestion_run_id TEXT NOT NULL,
  ingested_at TIMESTAMP NOT NULL DEFAULT NOW(),
  source TEXT NOT NULL,
  raw_json JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS bronze.ingestion_set_checkpoints (
  source TEXT NOT NULL,
  set_id TEXT NOT NULL,
  next_page INTEGER NOT NULL DEFAULT 1,
  completed BOOLEAN NOT NULL DEFAULT FALSE,
  last_error TEXT,
  last_ingestion_run_id TEXT,
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY (source, set_id)
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
