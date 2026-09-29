import sqlite3
from pathlib import Path

# 기존 데이터베이스 파일의 경로입니다.
db_path = Path(__file__).resolve().parent / "practice.db"

# 경로가 잘못됐을 때 빈 DB를 새로 만들지 않도록 확인합니다.
if not db_path.is_file():
    raise FileNotFoundError(f"데이터베이스가 없습니다: {db_path}")

conn = sqlite3.connect(db_path)

try:
    # 찾고 싶은 작성자를 지정합니다.
    target_author = "없는 작성자"

    # 작성자가 일치하는 행에서 본문과 작성자만 가져옵니다.
    cursor = conn.execute(
        "SELECT text, author FROM quotes WHERE author = ? ORDER BY id",
        (target_author,),
    )
    rows = cursor.fetchall()

    print("조회된 행 수:", len(rows))

    for text, author in rows:
        print("본문:", text)
        print("작성자:", author)

finally:
    conn.close()