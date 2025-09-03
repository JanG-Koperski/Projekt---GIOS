from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass(slots=True)
class Station:
    id: int
    code: str
    name: str
    lat: float
    lon: float
    city_id: int | None
    city_name: str | None
    commune: str | None
    district: str | None
    province: str | None
    street: str | None

@dataclass(slots=True)
class Sensor:
    id: int
    station_id: int
    param_name: str
    param_formula: str | None
    param_code: str
    param_id: int | None

@dataclass(slots=True)
class Measurement:
    sensor_id: int
    dt: datetime
    value: float | None

@dataclass
class AirIndex:
    station_id: int
    param: str             # np. SO2, NO2, PM10, PM2.5, O3, CO, C6H6
    value: float | None
    category: str | None
    calc_date: datetime | None
