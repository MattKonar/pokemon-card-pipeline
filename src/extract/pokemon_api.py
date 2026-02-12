import os
import random
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import requests
from requests.adapters import HTTPAdapter

BASE_URL = "https://api.pokemontcg.io/v2"
RETRYABLE_STATUS_CODES = (429, 500, 502, 503, 504)


def _headers() -> Dict[str, str]:
    api_key = os.getenv("POKEMON_TCG_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "POKEMON_TCG_API_KEY is required. Refusing to call the API without a key."
        )
    return {"X-Api-Key": api_key}


def _session() -> requests.Session:
    session = requests.Session()
    adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


SESSION = _session()


def _request_json_with_retries(
    path: str,
    params: Dict[str, Any],
    request_label: str,
) -> Dict[str, Any]:
    url = f"{BASE_URL}{path}"

    # Timeout tuple: (connect seconds, read seconds)
    connect_timeout = float(os.getenv("HTTP_CONNECT_TIMEOUT_SECONDS", "5"))
    read_timeout = float(os.getenv("HTTP_READ_TIMEOUT_SECONDS", "60"))
    timeout = (connect_timeout, read_timeout)

    max_attempts = int(os.getenv("HTTP_PAGE_MAX_ATTEMPTS", "10"))
    backoff_seconds = float(os.getenv("HTTP_PAGE_BACKOFF_SECONDS", "1"))
    max_backoff_seconds = float(os.getenv("HTTP_PAGE_MAX_BACKOFF_SECONDS", "60"))
    jitter_seconds = float(os.getenv("HTTP_PAGE_JITTER_SECONDS", "0.5"))

    for attempt in range(1, max_attempts + 1):
        try:
            resp = SESSION.get(url, params=params, headers=_headers(), timeout=timeout)
        except requests.exceptions.RequestException as exc:
            if attempt == max_attempts:
                raise
            sleep_for = backoff_seconds + random.uniform(0, jitter_seconds)
            print(
                f"Request error on {request_label} (attempt {attempt}/{max_attempts}): {exc}. "
                f"Sleeping {sleep_for:.1f}s before retry."
            )
            time.sleep(sleep_for)
            backoff_seconds = min(backoff_seconds * 2, max_backoff_seconds)
            continue

        if resp.status_code in RETRYABLE_STATUS_CODES:
            if attempt == max_attempts:
                resp.raise_for_status()

            retry_after = resp.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                sleep_for = float(retry_after)
            else:
                sleep_for = backoff_seconds + random.uniform(0, jitter_seconds)

            print(
                f"HTTP {resp.status_code} on {request_label} (attempt {attempt}/{max_attempts}). "
                f"Sleeping {sleep_for:.1f}s before retry."
            )
            time.sleep(sleep_for)
            backoff_seconds = min(backoff_seconds * 2, max_backoff_seconds)
            continue

        resp.raise_for_status()
        return resp.json()
    else:
        raise requests.exceptions.RetryError(f"Exhausted retries for {request_label}")

    raise RuntimeError(f"Unexpected retry flow for {request_label}")


def _meta_from_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "page": payload.get("page"),
        "pageSize": payload.get("pageSize"),
        "count": payload.get("count"),
        "totalCount": payload.get("totalCount"),
    }


def fetch_cards_page(
    page: int = 1,
    page_size: int = 250,
    query: Optional[str] = None,
    select_fields: Optional[Union[str, Sequence[str]]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    params: Dict[str, Any] = {"page": page, "pageSize": page_size}
    if query:
        params["q"] = query
    if select_fields:
        if isinstance(select_fields, str):
            params["select"] = select_fields
        else:
            params["select"] = ",".join(select_fields)

    label = f"cards page={page}"
    if query:
        label += f" q={query}"
    payload = _request_json_with_retries("/cards", params=params, request_label=label)
    cards = payload.get("data", [])
    meta = _meta_from_payload(payload)
    return cards, meta


def fetch_sets_page(page: int = 1, page_size: int = 250) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    params = {"page": page, "pageSize": page_size}
    payload = _request_json_with_retries("/sets", params=params, request_label=f"sets page={page}")
    sets = payload.get("data", [])
    meta = _meta_from_payload(payload)
    return sets, meta


def fetch_all_set_ids(page_size: int = 250) -> List[str]:
    page = 1
    expected_total = None
    set_ids: List[str] = []

    while True:
        sets, meta = fetch_sets_page(page=page, page_size=page_size)
        if not sets:
            break

        for set_obj in sets:
            set_id = set_obj.get("id")
            if set_id:
                set_ids.append(str(set_id))

        total_count = meta.get("totalCount")
        if total_count is not None:
            expected_total = int(total_count)

        if expected_total is not None and len(set_ids) >= expected_total:
            break
        page += 1

    return sorted(set(set_ids))
