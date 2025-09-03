from __future__ import annotations
import requests
from typing import Iterable, Dict, Any, List
from polair.utils import env_int, get_logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = get_logger(__name__)

BASE = "https://api.gios.gov.pl/pjp-api/v1/rest"
TIMEOUT = env_int("POLAIR_HTTP_TIMEOUT", 15)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((requests.RequestException,))
)



def _get_json(url, params=None, timeout=15):
    r = requests.get(url, params=params or {}, timeout=timeout)
    r.raise_for_status()
    return r.json()

class ApiError(RuntimeError):
    pass

def _check(resp: requests.Response) -> dict:
    if resp.status_code >= 400:
        raise ApiError(f"HTTP {resp.status_code}: {resp.text[:200]}")
    return resp.json()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8),
       retry=retry_if_exception_type((requests.RequestException, ApiError)))
def get_stations_page(page: int=0, size: int=200) -> dict:
    url = f"{BASE}/station/findAll?page={page}&size={size}"
    logger.info("GET %s", url)
    resp = requests.get(url, timeout=TIMEOUT)
    return _check(resp)

def iter_all_stations() -> Iterable[dict]:
    page = 0
    while True:
        data = get_stations_page(page=page, size=200)
        items = data.get("Lista stacji pomiarowych") or data.get("Lista stacji pomiarów") or []
        for it in items:
            yield it
        links = data.get("links") or {}
        if not links or "next" not in links or links["next"] == links.get("self"):
            break
        page += 1

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8),
       retry=retry_if_exception_type((requests.RequestException, ApiError)))
def get_sensors(station_id: int):


    page = 0
    size = 200
    out = []
    while True:
        url = f"{BASE}/station/sensors/{station_id}"
        data = _get_json(url, params={"page": page, "size": size})
        # <<< KLUCZ: bierzemy właściwą listę z wnętrza JSON-a >>>
        chunk = data.get("Lista stanowisk pomiarowych dla podanej stacji", [])
        if not isinstance(chunk, list):
            chunk = []
        out.extend(chunk)

        links = data.get("links", {})
        nxt = links.get("next")
        if not nxt or page >= data.get("totalPages", 1) - 1:
            break
        page += 1
        self.notebook.select(self.tab_measurements)



    return out

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8),
       retry=retry_if_exception_type((requests.RequestException, ApiError)))
def get_measurements(sensor_id: int) -> List[Dict[str, Any]]:

    url = f"{BASE}/data/getData/{sensor_id}"
    out: List[Dict[str, Any]] = []
    r = requests.get(url, timeout=15)
    if not r.ok:
        try:
            return r.json()  # tu często przychodzi ten "error_result"
        except Exception:
            r.raise_for_status()

    return r.json()

    while True:
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()

        # Jeśli API zwróci już listę – zwracamy ją
        if isinstance(data, list):
            out.extend(data)
            break

        # Format jak w Twoim zrzucie:
        if isinstance(data, dict):
            chunk = data.get("Lista danych pomiarowych", []) or []
            if isinstance(chunk, list):
                out.extend(chunk)

            links = data.get("links") or {}
            nxt = links.get("next")
            # Stop gdy nie ma next albo next == self
            if not nxt or nxt == links.get("self"):
                break


            url = nxt
            continue


        break

    return out

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8),
       retry=retry_if_exception_type((requests.RequestException, ApiError)))
def get_air_index(sensor_id: int) -> dict:

    url = f"{BASE}/aqindex/getIndex/{sensor_id}"
    logger.info("GET %s", url)
    resp = requests.get(url, timeout=TIMEOUT)
    return _check(resp)

def get_archival_measurements(sensor_id: int, date_from: str, date_to: str):
    """
    Pobiera dane archiwalne z API GIOS.
    date_from, date_to w formacie 'YYYY-MM-DD'
    """
    url = (
        f"https://api.gios.gov.pl/pjp-api/v1/rest/archivalData/getDataBySensor/{sensor_id}"
        f"?page=0&size=30&dateFrom={date_from}%2000%3A00&dateTo={date_to}%2000%3A00"
    )
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.json()

