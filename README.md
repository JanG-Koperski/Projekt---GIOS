# PolAir — Monitor jakości powietrza (GIOŚ)

Aplikacja desktopowa (Tkinter) do pobierania i analizowania danych o jakości powietrza w Polsce,
oparta o publiczne API GIOŚ.

## Funkcje
- Pobieranie listy stacji (z paginacją) oraz stanowisk/czujników i pomiarów.
- Zapisywanie stacji, stanowisk oraz danych pomiarowych do SQLite.
- Wczytywanie danych historycznych z bazy.
- Wykresy (matplotlib) wybranego czujnika z regulowanym zakresem czasu.
- Prosta analiza (min, max, średnia, trend liniowy z regresji).
- Wyszukiwanie stacji po mieście i w promieniu X km od podanej lokalizacji (geopy).
- Podgląd mapy stacji (folium) z kolorowaniem wg wartości wybranego parametru.
- Obsługa braku łączności i komunikaty o skorzystaniu z danych z bazy.

## Wymagania
- Python 3.10+ (Windows/Linux/macOS)
- Połączenie z Internetem (do pobierania danych z API)
- SQLite (wbudowane w Pythona)

## Instalacja
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows
# lub: source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

## Uruchomienie
```bash
python app.py
```
Na Windows można też użyć:
```cmd
run.bat
```

## Uruchomienie testów
```bash
pytest -q
```

## Konfiguracja
Plik bazy: `polair.db` w katalogu projektu (zmienna środowiskowa `POLAIR_DB_PATH` może wskazywać inny plik).
Czas timeout dla żądań HTTP: `POLAIR_HTTP_TIMEOUT` (domyślnie 15s).

## Architektura
- `polair/api.py` — klient REST do GIOŚ (paginacja, retry, walidacja).
- `polair/db.py` — warstwa dostępu do SQLite (DDL + helpery).
- `polair/models.py` — dataclasses reprezentujące encje.
- `polair/repository.py` — zapis/odczyt obiektów z bazy.
- `polair/services.py` — logika biznesowa i analiza danych.
- `polair/plotting.py` — generowanie wykresów (matplotlib).
- `polair/geo.py` — geolokalizacja i wyszukiwanie w promieniu (geopy).
- `polair/map.py` — render mapy (folium).
- `polair/utils.py` — narzędzia wspólne.
- `app.py` — GUI (Tkinter).

## Licencja
MIT
