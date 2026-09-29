import sqlite3
from pathlib import Path

# 현재 Python 파일과 같은 폴더에 데이터베이스를 저장합니다.
db_path = Path(__file__).resolve().parent / "practice.db"

# 데이터베이스에 연결합니다. 파일이 없으면 생성합니다.
conn = sqlite3.connect(db_path)

try:
    # quotes라는 이름의 테이블이 없을 때만 만듭니다.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY,
            text TEXT NOT NULL,
            author TEXT,
            source_url TEXT
        )
    """)

    # 변경 사항을 확정합니다.
    # 실제 인용문이 아닌, 저장 연습용 데이터입니다.
    sample = (
        "작은 단계로 나누어 연습합니다.",
        "연습용 작성자",
        "https://example.com/",
    )

    # 세 개의 ? 자리에 sample의 값을 순서대로 전달합니다.
    conn.execute(
        "INSERT INTO quotes (text, author, source_url) VALUES (?, ?, ?)",
        sample,
    )

    # 삽입한 데이터를 확정합니다.
    conn.commit()
    print("데이터 1건 저장 완료")

    # 테이블의 데이터를 id 순서대로 읽습니다.
    cursor = conn.execute(
        "SELECT id, text, author, source_url FROM quotes ORDER BY id"
    )
    rows = cursor.fetchall()

    for row in rows:
        print(row)

finally:
    # 작업이 끝나면 데이터베이스 연결을 닫습니다.
    conn.close()