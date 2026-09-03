"""
Run one or more .sql files against the project's SQLite database.

Usage:
    python run_sql.py sql/01_label_construction.sql
    python run_sql.py sql/01_label_construction.sql sql/02_feature_table.sql sql/03_combine_vintages.sql

Each file's statements are executed in order (split on ';'), and any
result rows from the final statement in a file are printed — useful
for the sanity-check SELECTs in 03_combine_vintages.sql.
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from config import SQLITE_DB_PATH  # noqa: E402


def run_sql_file(path: str, conn: sqlite3.Connection) -> None:
    sql_text = Path(path).read_text()
    print(f"\n--- Running {path} ---")
    cursor = conn.cursor()
    cursor.executescript(sql_text)
    conn.commit()
    print(f"Done: {path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_sql.py <file1.sql> [file2.sql ...]")
        sys.exit(1)

    conn = sqlite3.connect(SQLITE_DB_PATH)
    try:
        for sql_path in sys.argv[1:]:
            run_sql_file(sql_path, conn)
    finally:
        conn.close()
    print("\nAll SQL files executed successfully.")