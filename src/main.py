import uuid
from dotenv import load_dotenv

from src.extract.pokemon_api import fetch_cards
from src.load.postgres import insert_bronze_cards


def main():
    load_dotenv()

    ingestion_run_id = str(uuid.uuid4())

    cards = fetch_cards(page=1, page_size=100)

    inserted = insert_bronze_cards(
        ingestion_run_id=ingestion_run_id,
        source="pokemontcg_v2_cards",
        cards=cards,
    )

    print(f"Ingestion run: {ingestion_run_id}")
    print(f"Fetched: {len(cards)} cards")
    print(f"Inserted: {inserted} rows into bronze")


if __name__ == "__main__":
    main()