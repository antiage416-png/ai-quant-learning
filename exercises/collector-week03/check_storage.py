from storage import save_quotes

# 저장 함수의 동작을 확인하기 위한 가상 데이터입니다.
sample = {
    "text": "저장 함수 연결을 연습합니다.",
    "author": "연습용 작성자",
    "source_url": "https://example.com/",
    "published_at": None,
    "collected_at": "2026-09-29T00:00:00+00:00",
}

# 같은 데이터를 두 번 전달해 중복 저장 여부도 확인합니다.
records = [sample, sample.copy()]

# :memory:는 파일 대신 메모리에 만드는 임시 SQLite DB입니다.
total = save_quotes(records, db_path=":memory:")

print("전달한 명언 수:", len(records))
print("저장된 행 수:", total)