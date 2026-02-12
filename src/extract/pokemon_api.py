import os
from typing import Any, Dict, List

import requests


BASE_URL = "https://api.pokemontcg.io/v2"


def _headers() -> Dict[str, str]:
    api_key = os.getenv("POKEMON_TCG_API_KEY", "").strip()
    if api_key:
        return {"X-Api-Key": api_key}
    return {}


def fetch_cards(page: int = 1, page_size: int = 100) -> List[Dict[str, Any]]:
    url = f"{BASE_URL}/cards"
    params = {"page": page, "pageSize": page_size}

    response = requests.get(
        url,
        params=params,
        headers=_headers(),
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()
    return payload.get("data", [])