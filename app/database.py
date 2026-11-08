import sqlite3
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends

from app.config import settings


def get_db() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(settings.database_path, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


DBSession = Annotated[sqlite3.Connection, Depends(get_db)]
