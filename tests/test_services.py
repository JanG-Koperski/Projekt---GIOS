import pytest
from types import SimpleNamespace
from datetime import datetime
import polair.services  # Twój plik services.py
from polair import services



def parse_measurements_stub(rows, sensor_id):
    """
    Prosta wersja parse_measurements, która działa w testach.
    Tworzy SimpleNamespace zamiast modeli aplikacji.
    """
    result = []
    for r in rows:
        dt_str = r.get("Data")
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S") if dt_str else None
        except Exception:
            dt = None
        value = r.get("Wartość")
        result.append(SimpleNamespace(sensor_id=sensor_id, dt=dt, value=value))
    return result

def test_parse_measurements_basic():
    sample_data = [
        {
            "id": 123,
            "key": "PM10",
            "values": [
                {"date": "2025-08-20 12:00:00", "value": 42.5},
                {"date": "2025-08-20 13:00:00", "value": 43.1},
            ]
        }
    ]

    # Wywołanie stuba zamiast pełnej funkcji z aplikacji
    result = services.parse_measurements(sample_data)

    assert len(result) == 2
    assert result[0].sensor_id == 123
    # assert result[0].code == "PM10"
    assert result[0].value == 42.5
    assert result[1].value == 43.1


def test_parse_measurements_skip_none():
    # dane z None w wartości
    sample_data = [
        {
            "id": 456,
            "key": "PM2.5",
            "values": [
                {"date": "2025-08-20 12:00:00", "value": 50.0},
                {"date": "2025-08-20 13:00:00", "value": None},
            ]
        }
    ]

    result = services.parse_measurements(sample_data, sensor_id=456)

    assert len(result) == 1
    assert result[0].value == 50.0
    assert result[0].sensor_id == 456


def test_parse_measurements_empty_input():
    # pusta lista danych
    sample_data = []
    result = services.parse_measurements(sample_data)
    assert result == []


def test_parse_measurements_invalid_date():
    # błędny format daty
    sample_data = [
        {
            "id": 1,
            "key": "PM10",
            "values": [
                {"date": "not-a-date", "value": 10},
                {"date": "2025-08-20 15:00:00", "value": 20},
            ]
        }
    ]

    result = services.parse_measurements(sample_data, sensor_id=1)

    # funkcja powinna pominąć błędny rekord i zwrócić tylko poprawne
    assert len(result) == 1
    assert result[0].value == 20

def test_parse_measurements_invalid_record():
    sample_data = ["not-a-dict", None, 123]

    result = services.parse_measurements(sample_data)

    # wszystkie niepoprawne rekordy są pomijane
    assert result == []
