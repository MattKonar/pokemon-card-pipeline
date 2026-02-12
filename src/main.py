import os
import time
import uuid

from dotenv import load_dotenv

from src.extract.pokemon_api import fetch_cards_page
from src.load.postgres import insert_bronze_cards


def main() -> None:
    load_dotenv()

    ingestion_run_id = str(uuid.uuid4())

    page_size = int(os.getenv("PAGE_SIZE", "250"))
    max_pages_env = os.getenv("MAX_PAGES", "")
    max_pages = int(max_pages_env) if max_pages_env.strip() else None
    sleep_seconds = float(os.getenv("SLEEP_SECONDS", "0.2"))

    print(f"Ingestion run: {ingestion_run_id}")
    print(f"Config: PAGE_SIZE={page_size} MAX_PAGES={max_pages} SLEEP_SECONDS={sleep_seconds}")

    page = 1
    total_fetched = 0
    total_inserted = 0
    expected_total = None

    while True:
        if max_pages is not None and page > max_pages:
            print(f"Reached MAX_PAGES={max_pages}. Stopping.")
            break

        print(f"Fetching page {page}...")
        cards, meta = fetch_cards_page(page=page, page_size=page_size)

        got = len(cards)
        total_fetched += got

        total_count = meta.get("totalCount")
        if total_count is not None:
            expected_total = int(total_count)

        print(f"Fetched {got} cards on page {page}. totalCount={total_count}")

        if got == 0:
            print("No more cards returned. Stopping.")
            break

        inserted = insert_bronze_cards(
            ingestion_run_id=ingestion_run_id,
            source="pokemontcg_v2_cards",
            cards=cards,
        )
        total_inserted += inserted
        print(f"Inserted {inserted} rows. Run total inserted={total_inserted}.")

        if expected_total is not None and total_fetched >= expected_total:
            print(f"Reached totalCount={expected_total}. Stopping.")
            break

        page += 1
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    print("Done")
    print(f"Total fetched: {total_fetched}")
    print(f"Total inserted: {total_inserted}")


if __name__ == "__main__":
    main()