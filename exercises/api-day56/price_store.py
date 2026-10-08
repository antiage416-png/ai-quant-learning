# 목적: 실습용 DB에서 종목·기간에 해당하는 가격을 조회합니다.
# 입력 → 처리 → 결과: 종목코드·시작일·종료일 → SQL 조회 → 행 목록.
# DB를 읽기 전용으로 열며 파일 수정과 인터넷 요청은 없습니다.

import sqlite3
from datetime import date
from pathlib import Path

root = Path(__file__).resolve().parents[2]
DB_PATH = root / "data" / "stock-day56" / "prices.db"


# 날짜 객체 두 개를 받아 양 끝을 포함한 기간의 가격을 반환합니다.
def read_prices(stock_code: str, start_date: date, end_date: date):
    if not DB_PATH.is_file():
        raise FileNotFoundError(f"가격 DB가 없습니다: {DB_PATH}")

    # mode=ro는 읽기 전용이며, 경로가 틀려도 새 DB를 만들지 않습니다.
    connection = sqlite3.connect(
        DB_PATH.resolve().as_uri() + "?mode=ro",
        uri=True,
    )

    try:
        # 각 행을 열 이름으로 접근할 수 있도록 설정합니다.
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT stock_code, market, date,
                   open, high, low, close, volume
            FROM prices
            WHERE stock_code = ?
              AND date BETWEEN ? AND ?
            ORDER BY date
            """,
            (stock_code, start_date.isoformat(), end_date.isoformat()),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


# 직접 실행할 때만 작은 조회 예제를 확인합니다.
if __name__ == "__main__":
    prices = read_prices(
        "005930", date(2025, 1, 2), date(2025, 1, 6)
    )

    assert [row["date"] for row in prices] == [
        "2025-01-02", "2025-01-03", "2025-01-06"
    ]
    assert [row["close"] for row in prices] == [
        53400.0, 54400.0, 55900.0
    ]

    for row in prices:
        print("날짜:", row["date"], "종가:", row["close"])

    print("DB 종목·기간 조회 검사: 통과")