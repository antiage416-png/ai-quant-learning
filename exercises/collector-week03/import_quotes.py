import csv
from pathlib import Path
from storage import save_quotes

# 기존에 수집한 명언 20건의 CSV 경로입니다.
current_dir = Path(__file__).resolve().parent
csv_path = (
    current_dir.parent
    / "validation-day14"
    / "quotes_two_pages.csv"
)

records = []
skipped_count = 0

with csv_path.open(encoding="utf-8-sig", newline="") as file:
    # 열 이름을 키로 사용해 한 행씩 딕셔너리로 읽습니다.
    for row in csv.DictReader(file):
        # 본문과 작성자의 공백을 정리합니다.
        row["text"] = " ".join(row["text"].split())
        row["author"] = " ".join(row["author"].split())

        # 이번 저장 기준: 필수 정보가 없는 항목은 제외합니다.
        required = ["text", "author", "source_url", "collected_at"]

        if any(not row[column].strip() for column in required):
            skipped_count += 1
            continue

        # 발표 시각의 빈 문자열을 Python의 None으로 변환합니다.
        row["published_at"] = row["published_at"].strip() or None

        records.append(row)

# DB 경로를 생략했으므로 storage.py의 quotes.db에 저장합니다.
total = save_quotes(records)

print("저장에 전달한 명언 수:", len(records))
print("필수값 누락으로 제외:", skipped_count)
print("DB 전체 행 수:", total)