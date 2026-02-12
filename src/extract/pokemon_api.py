import os
import time
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


def fetch_cards_page(
    page: int = 1,
    page_size: int = 250,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    url = f"{BASE_URL}/cards"
    params = {"page": page, "pageSize": page_size}

    # Timeout tuple: (connect seconds, read seconds)
    timeout = (10, 120)

    # Extra safety retry loop for upstream 504/429 that can still happen even with adapter retries
    max_attempts = 6
    backoff_seconds = 1.0

    last_status = None
    for attempt in range(1, max_attempts + 1):
        resp = _session().get(url, params=params, headers=_headers(), timeout=timeout)
        last_status = resp.status_code

        # Success
        if 200 <= resp.status_code < 300:
            payload = resp.json()
            cards = payload.get("data", [])
            meta = {
                "page": payload.get("page"),
                "pageSize": payload.get("pageSize"),
                "count": payload.get("count"),
                "totalCount": payload.get("totalCount"),
            }
            return cards, meta

        # Retry on rate limiting and transient gateway/server errors
        if resp.status_code in (429, 500, 502, 503, 504):
            # Respect Retry-After when present
            retry_after = resp.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                sleep_for = float(retry_after)
            else:
                sleep_for = backoff_seconds

            print(
                f"HTTP {resp.status_code} on page {page} (attempt {attempt}/{max_attempts}). "
                f"Sleeping {sleep_for:.1f}s then retrying..."
            )
            time.sleep(sleep_for)
            backoff_seconds = min(backoff_seconds * 2, 30.0)
            continue

        # Non retryable status
        resp.raise_for_status()

    raise requests.exceptions.HTTPError(
        f"Failed to fetch page {page} after {max_attempts} attempts. Last status: {last_status}"
    )