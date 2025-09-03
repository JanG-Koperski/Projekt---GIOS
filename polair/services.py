from __future__ import annotations
from typing import List, Iterable, Tuple, Optional
from statistics import mean
from .models import Station, Sensor, Measurement
from dataclasses import dataclass
from types import SimpleNamespace
from datetime import datetime
# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# from polair import services

@dataclass
class Sensor:
    id: int
    station_id: int
    param_code: str
    param_name: str
    param_formula: str | None = None
    param_id: int | None = None



def parse_station(rec: dict) -> Station:
    # Obsługa kluczy wg dostarczonej struktury PL
    return Station(
        id=int(rec.get("Identyfikator stacji")),
        code=str(rec.get("Kod stacji")),
        name=str(rec.get("Nazwa stacji")),
        lat=float(rec.get("WGS84 φ N")),
        lon=float(rec.get("WGS84 λ E")),
        city_id=int(rec.get("Identyfikator miasta")) if rec.get("Identyfikator miasta") is not None else None,
        city_name=rec.get("Nazwa miasta"),
        commune=rec.get("Gmina"),
        district=str(rec.get("Powiat")),
        province=rec.get("Województwo"),
        street=rec.get("Ulica")
    )

def parse_sensor(rec: dict) -> Sensor:

    if not isinstance(rec, dict):
        raise TypeError(f"parse_sensor: oczekiwano dict, dostałem {type(rec).__name__}")


    if "param" in rec and isinstance(rec.get("param"), dict):
        p = rec["param"]
        return Sensor(
            id=int(rec.get("id")),
            station_id=int(rec.get("stationId")),
            param_code=str(p.get("paramCode") or ""),
            param_name=str(p.get("paramName") or ""),
            param_formula=p.get("paramFormula"),
            param_id=int(p["idParam"]) if p.get("idParam") is not None else None,
        )


    return Sensor(
        id=int(rec.get("Identyfikator stanowiska")),
        station_id=int(rec.get("Identyfikator stacji")),
        param_code=str(rec.get("Wskaźnik - kod") or ""),
        param_name=str(rec.get("Wskaźnik") or ""),
        param_formula=rec.get("Wskaźnik - wzór"),
    )

def parse_measurements(data, sensor_id=None):
    ms = []
    if not data:
        return ms


    if isinstance(data, list):
        records = data
    else:
        records = [data]

    for rec in records:
        if not isinstance(rec, dict):
            continue

        vals = rec.get("values") or []
        key = rec.get("key") or rec.get("code") or "unknown"

        for v in vals:
            val = v.get("value")
            dt = v.get("date")

            if val is None:
                continue

            # 🔹 sprawdzenie poprawności daty
            try:
                datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue

            m = Measurement(
                sensor_id=rec.get("id") or sensor_id,
                dt=dt,
                value=val,
                # jeśli zdecydujesz się dodać:
                # code=key
            )
            ms.append(m)

    return ms


def simple_stats(ms: Iterable[Measurement]) -> dict:
    filt = [m for m in ms if m.value is not None]
    if not filt:
        return {"min": None, "min_at": None, "max": None, "max_at": None, "avg": None, "trend_slope": None}
    min_m = min(filt, key=lambda m: m.value)
    max_m = max(filt, key=lambda m: m.value)
    avg = mean(m.value for m in filt)


    xs = list(range(len(filt)))
    ys = [m.value for m in filt]
    n = len(xs)
    sumx = sum(xs); sumy = sum(ys)
    sumxy = sum(x*y for x,y in zip(xs, ys))
    sumx2 = sum(x*x for x in xs)
    denom = n*sumx2 - sumx*sumx
    slope = (n*sumxy - sumx*sumy)/denom if denom != 0 else 0.0

    return {
        "min": min_m.value, "min_at": min_m.dt,
        "max": max_m.value, "max_at": max_m.dt,
        "avg": avg, "trend_slope": slope
    }
