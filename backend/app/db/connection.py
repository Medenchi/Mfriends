import sqlite3
from collections.abc import Generator
from pathlib import Path

from backend.app.core.config import get_settings


def ensure_database_parent() -> None:
    settings = get_settings()
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)


def connect() -> sqlite3.Connection:
    ensure_database_parent()
    connection = sqlite3.connect(get_settings().database_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    return connection


def get_db() -> Generator[sqlite3.Connection, None, None]:
    connection = connect()
    try:
        yield connection
    finally:
        connection.close()
