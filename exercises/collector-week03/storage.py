import sqlite3
from pathlib import Path

# 통합 수집기에서 사용할 DB 위치입니다.
DB_PATH = Path(__file__).resolve().parent / "quotes.db"


def save_quotes(records, db_path=DB_PATH):
    """명언 목록을 저장하고 DB의 전체 행 수를 반환합니다."""
    conn = sqlite3.connect(db_path)

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY,
                text TEXT NOT NULL,
                author TEXT NOT NULL,
                source_url TEXT NOT NULL,
                published_at TEXT,
                collected_at TEXT NOT NULL,
                UNIQUE(text, author)
            )
        """)

        for record in records:
            conn.execute("""
                INSERT INTO quotes (
                    text, author, source_url,
                    published_at, collected_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(text, author)
                DO UPDATE SET
                    source_url = excluded.source_url,
                    published_at = excluded.published_at,
                    collected_at = excluded.collected_at
            """, (
                record["text"],
                record["author"],
                record["source_url"],
                record["published_at"],
                record["collected_at"],
            ))

        conn.commit()

        total = conn.execute(
            "SELECT COUNT(*) FROM quotes"
        ).fetchone()[0]

        return total

    finally:
        conn.close()