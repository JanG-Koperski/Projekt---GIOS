from __future__ import annotations
import sqlite3
from typing import Iterable, Sequence, Any
from polair.utils import env_int, get_logger
from polair.utils import env_str

logger = get_logger(__name__)

def get_conn(path: str | None = None) -> sqlite3.Connection:
    db_path = path or env_str("POLAIR_DB_PATH", "polair.db")
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

DDL = [
    """
    CREATE TABLE IF NOT EXISTS stations (
        id INTEGER PRIMARY KEY,
        code TEXT,
        name TEXT,
        lat REAL,
        lon REAL,
        city_id INTEGER,
        city_name TEXT,
        commune TEXT,
        district TEXT,
        province TEXT,
        street TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sensors (
        id INTEGER PRIMARY KEY,
        station_id INTEGER NOT NULL,
        param_name TEXT,
        param_formula TEXT,
        param_code TEXT,
        param_id INTEGER,
        FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS measurements (
        sensor_id INTEGER NOT NULL,
        dt TEXT NOT NULL,
        value REAL,
        PRIMARY KEY (sensor_id, dt),
        FOREIGN KEY (sensor_id) REFERENCES sensors(id) ON DELETE CASCADE
    );
    """
]

def init_db(conn: sqlite3.Connection) -> None:
    for stmt in DDL:
        conn.execute(stmt)
    conn.commit()

def executemany(conn: sqlite3.Connection, sql: str, rows: Iterable[Sequence[Any]]) -> None:
    conn.executemany(sql, rows)
    conn.commit()

def ensure_schema(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensors (
            id INTEGER PRIMARY KEY,
            station_id INTEGER,
            param_code TEXT,
            param_name TEXT,
            param_formula TEXT,
            param_id INTEGER
        )
    """)
    conn.commit()


