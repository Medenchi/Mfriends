from pathlib import Path

from backend.app.db.connection import connect


def init_db() -> None:
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with connect() as connection:
        connection.executescript(schema)


if __name__ == "__main__":
    init_db()
