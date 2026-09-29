import sqlite3
from pathlib import Path

# 어제의 DB와 구분되는 새 연습용 DB입니다.
db_path = Path(__file__).resolve().parent / "practice.db"
conn = sqlite3.connect(db_path)

try:
    # 본문과 작성자의 조합이 중복되지 않도록 설정합니다.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY,
            text TEXT NOT NULL,
            author TEXT NOT NULL,
            source_url TEXT,
            UNIQUE(text, author)
        )
    """)

    # 본문·작성자는 같고, 출처 주소만 변경한 연습 데이터입니다.
    sample = (
        "작은 단계로 나누어 연습합니다.",
        "연습용 작성자",
        "https://example.com/updated",
    )

    # 새 명언이면 삽입하고,
    # 같은 본문·작성자가 이미 있으면 출처 주소를 갱신합니다.
    conn.execute("""
        INSERT INTO quotes (text, author, source_url)
        VALUES (?, ?, ?)
        ON CONFLICT(text, author)
        DO UPDATE SET source_url = excluded.source_url
    """, sample)

    conn.commit()

    rows = conn.execute(
        "SELECT id, text, author, source_url FROM quotes ORDER BY id"
    ).fetchall()

    print("저장된 행 수:", len(rows))

    for row in rows:
        print(row)

finally:
    conn.close()