import os
from typing import Any, Dict, List, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://api.pokemontcg.io/v2"


def _headers() -> Dict[str, str]:
    api_key = os.getenv("POKEMON_TCG_API_KEY", "").strip()
    if api_key:
        return {"X-Api-Key": api_key}
    return {}


def _session() -> requests.Session:
    """Requests session with retries for transient failures and rate limits."""
    session = requests.Session()

    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_cards_page(page: int = 1, page_size: int = 250) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Fetch one page of cards from the Pokemon TCG API.

    Returns (cards, meta) where meta includes page, pageSize, count, totalCount when provided.
    """
    url = f"{BASE_URL}/cards"
    params = {"page": page, "pageSize": page_size}

    # Timeout tuple: (connect seconds, read seconds)
    timeout = (10, 120)

    resp = _session().get(url, params=params, headers=_headers(), timeout=timeout)
    resp.raise_for_status()

    payload = resp.json()
    cards = payload.get("data", [])
    meta = {
        "page": payload.get("page"),
        "pageSize": payload.get("pageSize"),
        "count": payload.get("count"),
        "totalCount": payload.get("totalCount"),
    }
    return cards, meta