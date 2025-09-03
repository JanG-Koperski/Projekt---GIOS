from __future__ import annotations
import sqlite3
from typing import Iterable, Sequence, List, Optional
from .models import Station, Sensor, Measurement
from .db import executemany
from datetime import datetime
from . import db

def upsert_stations(conn: sqlite3.Connection, stations: Iterable[Station]) -> None:
    sql = """
    INSERT INTO stations (id, code, name, lat, lon, city_id, city_name, commune, district, province, street)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        code=excluded.code, name=excluded.name, lat=excluded.lat, lon=excluded.lon,
        city_id=excluded.city_id, city_name=excluded.city_name,
        commune=excluded.commune, district=excluded.district,
        province=excluded.province, street=excluded.street;
    """
    rows = [(s.id, s.code, s.name, s.lat, s.lon, s.city_id, s.city_name, s.commune, s.district, s.province, s.street) for s in stations]
    executemany(conn, sql, rows)

def upsert_sensors(conn: sqlite3.Connection, sensors: Iterable[Sensor]) -> None:
    sql = """
    INSERT INTO sensors (id, station_id, param_name, param_formula, param_code, param_id)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        station_id=excluded.station_id, param_name=excluded.param_name,
        param_formula=excluded.param_formula, param_code=excluded.param_code, param_id=excluded.param_id;
    """
    rows = [(x.id, x.station_id, x.param_name, x.param_formula, x.param_code, x.param_id) for x in sensors]
    executemany(conn, sql, rows)

def upsert_measurements(conn: sqlite3.Connection, ms: Iterable[Measurement]) -> None:
    sql = """
    INSERT INTO measurements (sensor_id, dt, value) VALUES (?, ?, ?)
    ON CONFLICT(sensor_id, dt) DO UPDATE SET value=excluded.value;
    """
    rows = [(m.sensor_id, m.dt.isoformat(), m.value) for m in ms]
    executemany(conn, sql, rows)

def ensure_schema(conn):
    return db.ensure_schema(conn)

def get_stations(conn: sqlite3.Connection, city_name_like: Optional[str] = None) -> list[Station]:
    cur = conn.cursor()
    if city_name_like:
        cur.execute("SELECT id, code, name, lat, lon, city_id, city_name, commune, district, province, street FROM stations WHERE city_name LIKE ? ORDER BY city_name, name", (f"%{city_name_like}%",))
    else:
        cur.execute("SELECT id, code, name, lat, lon, city_id, city_name, commune, district, province, street FROM stations ORDER BY province, city_name, name")
    rows = cur.fetchall()
    return [Station(*row) for row in rows]

def get_sensors_by_station(conn: sqlite3.Connection, station_id: int) -> list[Sensor]:
    cur = conn.cursor()
    cur.execute("SELECT id, station_id, param_name, param_formula, param_code, param_id FROM sensors WHERE station_id=? ORDER BY param_code", (station_id,))
    rows = cur.fetchall()
    return [Sensor(*row) for row in rows]

def get_measurements(conn: sqlite3.Connection, sensor_id: int, since_iso: Optional[str] = None) -> list[Measurement]:
    cur = conn.cursor()
    if since_iso:
        cur.execute("SELECT sensor_id, dt, value FROM measurements WHERE sensor_id=? AND dt>=? ORDER BY dt", (sensor_id, since_iso))
    else:
        cur.execute("SELECT sensor_id, dt, value FROM measurements WHERE sensor_id=? ORDER BY dt", (sensor_id,))
    rows = cur.fetchall()
    from datetime import datetime
    return [Measurement(sensor_id=row[0], dt=datetime.fromisoformat(row[1]), value=row[2]) for row in rows]

def upsert_air_index(conn, indexes: list[AirIndex]):
    c = conn.cursor()
    for idx in indexes:
        c.execute("""
            INSERT INTO air_index (station_id, param, value, category, calc_date)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(station_id, param) DO UPDATE SET
                value=excluded.value,
                category=excluded.category,
                calc_date=excluded.calc_date
        """, (idx.station_id, idx.param, idx.value, idx.category, idx.calc_date.isoformat() if idx.calc_date else None))
    conn.commit()

