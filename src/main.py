import os
import time
import uuid

from dotenv import load_dotenv

from src.extract.pokemon_api import fetch_all_set_ids, fetch_cards_page
from src.load.postgres import (
    ensure_checkpoint_table,
    get_set_checkpoints,
    insert_bronze_cards,
    upsert_set_checkpoint,
)

SOURCE_NAME = "pokemontcg_v2_cards"


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _truncate_error(exc: Exception, max_len: int = 2000) -> str:
    value = f"{type(exc).__name__}: {exc}"
    if len(value) <= max_len:
        return value
    return f"{value[: max_len - 3]}..."


def main() -> None:
    load_dotenv()

    if not os.getenv("POKEMON_TCG_API_KEY", "").strip():
        raise RuntimeError(
            "POKEMON_TCG_API_KEY is required. Set it in .env or your environment before running."
        )
    ensure_checkpoint_table()

    ingestion_run_id = str(uuid.uuid4())

    page_size = int(os.getenv("PAGE_SIZE", "100"))
    sets_page_size = int(os.getenv("SETS_PAGE_SIZE", "250"))
    max_sets_env = os.getenv("MAX_SETS", "")
    max_sets = int(max_sets_env) if max_sets_env.strip() else None
    sleep_seconds = float(os.getenv("SLEEP_SECONDS", "0.1"))
    reprocess_completed = _env_bool("REPROCESS_COMPLETED", default=False)
    stop_on_set_error = _env_bool("STOP_ON_SET_ERROR", default=False)
    fail_on_any_failure = _env_bool("FAIL_ON_ANY_FAILURE", default=False)
    select_fields = os.getenv("CARD_SELECT_FIELDS", "").strip() or None
    only_set_ids_env = os.getenv("ONLY_SET_IDS", "").strip()
    only_set_ids = {value.strip() for value in only_set_ids_env.split(",") if value.strip()}

    print(f"Ingestion run: {ingestion_run_id}")
    print(
        "Config: "
        f"PAGE_SIZE={page_size} "
        f"SETS_PAGE_SIZE={sets_page_size} "
        f"MAX_SETS={max_sets} "
        f"SLEEP_SECONDS={sleep_seconds} "
        f"REPROCESS_COMPLETED={reprocess_completed} "
        f"STOP_ON_SET_ERROR={stop_on_set_error}"
    )

    set_ids = fetch_all_set_ids(page_size=sets_page_size)
    if only_set_ids:
        set_ids = [set_id for set_id in set_ids if set_id in only_set_ids]
    if max_sets is not None:
        set_ids = set_ids[:max_sets]

    if not set_ids:
        print("No sets to process. Done.")
        return

    total_fetched = 0
    total_inserted = 0
    completed_sets = 0
    failed_sets = 0
    skipped_sets = 0

    checkpoints = get_set_checkpoints(source=SOURCE_NAME)

    for index, set_id in enumerate(set_ids, start=1):
        checkpoint = checkpoints.get(set_id, {})
        checkpoint_completed = bool(checkpoint.get("completed", False))
        checkpoint_next_page = int(checkpoint.get("next_page", 1))

        if checkpoint_completed and not reprocess_completed:
            skipped_sets += 1
            print(f"[{index}/{len(set_ids)}] Set {set_id} already complete. Skipping.")
            continue

        page = 1 if reprocess_completed else max(1, checkpoint_next_page)
        set_fetched = 0
        set_inserted = 0
        set_expected_total = None
        set_query = f"set.id:{set_id}"

        print(f"[{index}/{len(set_ids)}] Processing set {set_id} starting at page {page}...")

        upsert_set_checkpoint(
            source=SOURCE_NAME,
            set_id=set_id,
            next_page=page,
            completed=False,
            ingestion_run_id=ingestion_run_id,
            last_error=None,
        )

        try:
            while True:
                cards, meta = fetch_cards_page(
                    page=page,
                    page_size=page_size,
                    query=set_query,
                    select_fields=select_fields,
                )

                got = len(cards)
                set_fetched += got
                total_fetched += got

                total_count = meta.get("totalCount")
                if total_count is not None:
                    set_expected_total = int(total_count)

                print(
                    f"Set {set_id} page {page}: fetched={got} "
                    f"set_total={set_expected_total}"
                )

                if got == 0:
                    upsert_set_checkpoint(
                        source=SOURCE_NAME,
                        set_id=set_id,
                        next_page=page,
                        completed=True,
                        ingestion_run_id=ingestion_run_id,
                        last_error=None,
                    )
                    completed_sets += 1
                    print(
                        f"Set {set_id} completed at page {page}. "
                        f"set_fetched={set_fetched} set_inserted={set_inserted}."
                    )
                    break

                inserted = insert_bronze_cards(
                    ingestion_run_id=ingestion_run_id,
                    source=SOURCE_NAME,
                    cards=cards,
                )
                set_inserted += inserted
                total_inserted += inserted

                next_page = page + 1
                upsert_set_checkpoint(
                    source=SOURCE_NAME,
                    set_id=set_id,
                    next_page=next_page,
                    completed=False,
                    ingestion_run_id=ingestion_run_id,
                    last_error=None,
                )
                print(f"Set {set_id} page {page}: inserted={inserted}. next_page={next_page}.")

                if set_expected_total is not None and set_fetched >= set_expected_total:
                    upsert_set_checkpoint(
                        source=SOURCE_NAME,
                        set_id=set_id,
                        next_page=next_page,
                        completed=True,
                        ingestion_run_id=ingestion_run_id,
                        last_error=None,
                    )
                    completed_sets += 1
                    print(
                        f"Set {set_id} completed by totalCount. "
                        f"set_fetched={set_fetched} set_inserted={set_inserted}."
                    )
                    break

                page = next_page
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
        except Exception as exc:
            failed_sets += 1
            error_message = _truncate_error(exc)
            upsert_set_checkpoint(
                source=SOURCE_NAME,
                set_id=set_id,
                next_page=page,
                completed=False,
                ingestion_run_id=ingestion_run_id,
                last_error=error_message,
            )
            print(f"Set {set_id} failed at page {page}: {error_message}")
            if stop_on_set_error:
                raise

    print("Done")
    print(f"Total fetched: {total_fetched}")
    print(f"Total inserted: {total_inserted}")
    print(
        f"Sets summary: completed={completed_sets} skipped={skipped_sets} failed={failed_sets} "
        f"total_target_sets={len(set_ids)}"
    )

    if failed_sets > 0 and fail_on_any_failure:
        raise RuntimeError(f"{failed_sets} set(s) failed. Check logs and checkpoints table.")


if __name__ == "__main__":
    main()
