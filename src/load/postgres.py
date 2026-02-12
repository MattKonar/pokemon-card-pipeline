import os
import json
from typing import Any, Dict, Iterable

from sqlalchemy import create_engine, text


def get_engine():
    user = os.getenv("POSTGRES_USER", "pokemon")
    password = os.getenv("POSTGRES_PASSWORD", "pokemon")
    db = os.getenv("POSTGRES_DB", "pokemon")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")

    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    return create_engine(url, future=True)


def insert_bronze_cards(
    ingestion_run_id: str,
    source: str,
    cards: Iterable[Dict[str, Any]],
) -> int:

    engine = get_engine()

    sql = text(
        """
        INSERT INTO bronze.pokemon_cards_raw
            (ingestion_run_id, source, card_id, raw_json)
        VALUES
            (:ingestion_run_id, :source, :card_id, CAST(:raw_json AS jsonb))
        ON CONFLICT (ingestion_run_id, card_id) DO NOTHING
        """
    )

    inserted = 0

    with engine.begin() as conn:
        for card in cards:
            card_id = card.get("id")
            if not card_id:
                continue

            conn.execute(
                sql,
                {
                    "ingestion_run_id": ingestion_run_id,
                    "source": source,
                    "card_id": card_id,
                    "raw_json": json.dumps(card),
                },
            )
            inserted += 1

    return inserted