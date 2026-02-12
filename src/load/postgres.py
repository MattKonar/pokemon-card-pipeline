import json
import os
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import create_engine, text

_ENGINE = None


def get_engine():
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE

    user = os.getenv("POSTGRES_USER", "pokemon")
    password = os.getenv("POSTGRES_PASSWORD", "pokemon")
    db = os.getenv("POSTGRES_DB", "pokemon")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")

    url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"
    _ENGINE = create_engine(url, future=True, pool_pre_ping=True)
    return _ENGINE


def ensure_checkpoint_table() -> None:
    create_schema_sql = text("CREATE SCHEMA IF NOT EXISTS bronze")
    create_table_sql = text(
        """
        CREATE TABLE IF NOT EXISTS bronze.ingestion_set_checkpoints (
            source TEXT NOT NULL,
            set_id TEXT NOT NULL,
            next_page INTEGER NOT NULL DEFAULT 1,
            completed BOOLEAN NOT NULL DEFAULT FALSE,
            last_error TEXT,
            last_ingestion_run_id TEXT,
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            PRIMARY KEY (source, set_id)
        )
        """
    )

    with get_engine().begin() as conn:
        conn.execute(create_schema_sql)
        conn.execute(create_table_sql)


def get_set_checkpoints(source: str) -> Dict[str, Dict[str, Any]]:
    sql = text(
        """
        SELECT
            set_id,
            next_page,
            completed,
            last_error,
            last_ingestion_run_id,
            updated_at
        FROM bronze.ingestion_set_checkpoints
        WHERE source = :source
        """
    )

    with get_engine().begin() as conn:
        rows = conn.execute(sql, {"source": source}).mappings().all()

    checkpoints: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        checkpoints[str(row["set_id"])] = {
            "next_page": int(row["next_page"]),
            "completed": bool(row["completed"]),
            "last_error": row["last_error"],
            "last_ingestion_run_id": row["last_ingestion_run_id"],
            "updated_at": row["updated_at"],
        }
    return checkpoints


def upsert_set_checkpoint(
    source: str,
    set_id: str,
    next_page: int,
    completed: bool,
    ingestion_run_id: str,
    last_error: Optional[str] = None,
) -> None:
    sql = text(
        """
        INSERT INTO bronze.ingestion_set_checkpoints
            (source, set_id, next_page, completed, last_error, last_ingestion_run_id)
        VALUES
            (:source, :set_id, :next_page, :completed, :last_error, :last_ingestion_run_id)
        ON CONFLICT (source, set_id)
        DO UPDATE SET
            next_page = EXCLUDED.next_page,
            completed = EXCLUDED.completed,
            last_error = EXCLUDED.last_error,
            last_ingestion_run_id = EXCLUDED.last_ingestion_run_id,
            updated_at = NOW()
        """
    )

    with get_engine().begin() as conn:
        conn.execute(
            sql,
            {
                "source": source,
                "set_id": set_id,
                "next_page": max(1, int(next_page)),
                "completed": completed,
                "last_error": last_error,
                "last_ingestion_run_id": ingestion_run_id,
            },
        )


def insert_bronze_cards(
    ingestion_run_id: str,
    source: str,
    cards: Iterable[Dict[str, Any]],
) -> int:
    sql = text(
        """
        INSERT INTO bronze.pokemon_cards_raw
            (card_id, last_ingestion_run_id, source, raw_json)
        VALUES
            (:card_id, :last_ingestion_run_id, :source, CAST(:raw_json AS jsonb))
        ON CONFLICT (card_id)
        DO UPDATE SET
            last_ingestion_run_id = EXCLUDED.last_ingestion_run_id,
            ingested_at = NOW(),
            source = EXCLUDED.source,
            raw_json = EXCLUDED.raw_json
        """
    )

    payload: List[Dict[str, Any]] = []
    for card in cards:
        card_id = card.get("id")
        if not card_id:
            continue
        payload.append(
            {
                "card_id": card_id,
                "last_ingestion_run_id": ingestion_run_id,
                "source": source,
                "raw_json": json.dumps(card),
            }
        )

    if not payload:
        return 0

    with get_engine().begin() as conn:
        conn.execute(sql, payload)

    return len(payload)
