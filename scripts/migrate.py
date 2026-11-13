import sqlite3
from pathlib import Path

from app.config import settings

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "sql" / "migrations"


def migrate(db_path: Path) -> list[str]:
    """Apply every migration file that has not been applied yet."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "version TEXT PRIMARY KEY, "
        "applied_at TEXT NOT NULL DEFAULT (datetime('now')))"
    )
    conn.commit()
    applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}

    ran: list[str] = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if path.stem in applied:
            continue
        # path.stem is a file name from our own repo, not user input.
        script = (
            "BEGIN;\n"
            + path.read_text()
            + f"\nINSERT INTO schema_migrations (version) VALUES ('{path.stem}');\n"
            + "COMMIT;"
        )
        try:
            conn.executescript(script)
        except sqlite3.Error:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        ran.append(path.stem)

    conn.close()
    return ran


if __name__ == "__main__":
    done = migrate(settings.database_path)
    print("Applied: " + ", ".join(done) if done else "Nothing to migrate")
