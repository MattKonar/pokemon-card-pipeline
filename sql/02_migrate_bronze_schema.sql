BEGIN;

CREATE TABLE IF NOT EXISTS bronze.pokemon_cards_raw_new (
  card_id TEXT PRIMARY KEY,
  last_ingestion_run_id TEXT NOT NULL,
  ingested_at TIMESTAMP NOT NULL DEFAULT NOW(),
  source TEXT NOT NULL,
  raw_json JSONB NOT NULL
);

INSERT INTO bronze.pokemon_cards_raw_new (card_id, last_ingestion_run_id, ingested_at, source, raw_json)
SELECT DISTINCT ON (card_id)
  card_id,
  ingestion_run_id AS last_ingestion_run_id,
  ingested_at,
  source,
  raw_json
FROM bronze.pokemon_cards_raw
ORDER BY card_id, ingested_at DESC;

DROP TABLE bronze.pokemon_cards_raw;
ALTER TABLE bronze.pokemon_cards_raw_new RENAME TO pokemon_cards_raw;

COMMIT;
