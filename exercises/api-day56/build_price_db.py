# 목적: 56일차 실습용 SQLite DB와 주가 테이블을 준비합니다.
# 입력 → 처리 → 결과: 열·고유키 정의 → DB 연결 → 테이블 생성.
# 로컬 DB를 생성하며 원본 CSV 수정과 인터넷 요청은 없습니다.

import sqlite3
from pathlib import Path
import pandas as pd

# 실행한 터미널 위치와 관계없이 프로젝트 폴더를 찾습니다.
root = Path(__file__).resolve().parents[2]
output_dir = root / "data" / "stock-day56"
output_dir.mkdir(parents=True, exist_ok=True)
db_path = output_dir / "prices.db"

# 저장할 열의 순서를 DB 테이블과 동일하게 맞춥니다.
columns = [
    "stock_code", "market", "date",
    "open", "high", "low", "close", "volume",
]
prepared_tables = []

# 두 종목의 개발 기간 자료만 준비합니다.
for stock_code in ["005930", "000660"]:
    csv_path = (
        root / "data" / "stock-day33" / "clean"
        / f"{stock_code}_2025_clean.csv"
    )
    table = pd.read_csv(csv_path, dtype={"stock_code": str})

    # 필수 열과 종목이 예상대로인지 먼저 확인합니다.
    assert set(columns).issubset(table.columns), "필수 열이 없습니다."
    assert table["stock_code"].eq(stock_code).all(), "종목이 섞여 있습니다."
    assert table["market"].eq("KRX").all(), "시장 값이 예상과 다릅니다."

    dates = pd.to_datetime(
        table["date"], format="%Y-%m-%d", errors="raise"
    )
    assert dates.notna().all(), "날짜가 빠진 행이 있습니다."

    # 원본 표와 분리된 복사본을 만들고 날짜 형식을 통일합니다.
    selected = table.loc[
        dates.between("2025-01-02", "2025-06-30"), columns
    ].copy()
    selected["date"] = dates.loc[selected.index].dt.strftime("%Y-%m-%d")
    selected = selected.sort_values("date")

    # 46일차에서 확인한 개발 기간의 행 수와 경계를 대조합니다.
    assert len(selected) == 118, "개발 기간의 행 수가 다릅니다."
    assert selected["date"].iloc[0] == "2025-01-02"
    assert selected["date"].iloc[-1] == "2025-06-30"
    assert not selected.duplicated(["stock_code", "date"]).any(), (
        "같은 종목·날짜가 중복됐습니다."
    )
    assert selected.notna().all().all(), "저장할 자료에 결측값이 있습니다."

    prepared_tables.append(selected)
    print(f"{stock_code} 저장 준비 행 수:", len(selected))

# 두 종목의 표를 합치고 행 번호를 새로 붙입니다.
prepared = pd.concat(prepared_tables, ignore_index=True)
print("전체 저장 준비 행 수:", len(prepared))

# SQLite는 지정한 DB 파일이 없으면 새로 만듭니다.
connection = sqlite3.connect(db_path)


try:
    # 같은 종목의 같은 날짜가 중복되지 않도록 복합 기본키를 둡니다.
    connection.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            stock_code TEXT NOT NULL,
            market TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER NOT NULL,
            PRIMARY KEY (stock_code, date)
        )
    """)
    connection.commit()

        # 준비한 표를 행별 값 묶음으로 변환합니다.
    records = list(prepared.itertuples(index=False, name=None))

    # 성공하면 저장을 확정하고, 실패하면 이번 변경을 되돌립니다.
    with connection:
        connection.executemany("""
            INSERT INTO prices (
                stock_code, market, date,
                open, high, low, close, volume
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(stock_code, date) DO UPDATE SET
                market = excluded.market,
                open = excluded.open,
                high = excluded.high,
                low = excluded.low,
                close = excluded.close,
                volume = excluded.volume
        """, records)

    print("저장 처리한 입력 행 수:", len(records))    

    # 현재 저장된 행 수를 조회합니다.
    row_count = connection.execute(
        "SELECT COUNT(*) FROM prices"
    ).fetchone()[0]

    print("DB 저장 위치:", db_path)
    print("현재 가격 행 수:", row_count)

    # DB에서 두 종목의 개발 기간 자료를 날짜순으로 다시 읽습니다.
    restored = pd.read_sql_query(
        """
        SELECT stock_code, market, date,
               open, high, low, close, volume
        FROM prices
        WHERE stock_code IN (?, ?)
          AND date BETWEEN ? AND ?
        ORDER BY stock_code, date
        """,
        connection,
        params=("005930", "000660", "2025-01-02", "2025-06-30"),
    )

    # CSV에서 준비한 표도 같은 순서와 행 번호로 맞춥니다.
    expected = prepared.sort_values(
        ["stock_code", "date"]
    ).reset_index(drop=True)

    # CSV의 정수 가격과 DB의 REAL 가격을 같은 자료형으로 맞춥니다.
    price_columns = ["open", "high", "low", "close"]
    expected[price_columns] = expected[price_columns].astype(float)
    expected["volume"] = expected["volume"].astype("int64")

    # 열·행·자료형·전체 값이 같은지 확인합니다.
    pd.testing.assert_frame_equal(
        restored, expected, check_exact=True
    )

    print("DB 재조회 행 수:", len(restored))
    print("CSV 준비 자료와 DB 전체 값 대조: 통과")

finally:
    # 작업이 실패해도 DB 연결은 닫습니다.
    connection.close()