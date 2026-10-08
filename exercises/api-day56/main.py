# 목적: DB 기반 분석 API에 필요한 조회 함수와 기존 계산 기준을 준비합니다.
# 입력 → 처리 → 결과: 기존 코드 경로 → 모듈 불러오기 → 함수·거래일 기준 연결.
# 이 준비 단계에서는 DB 저장과 인터넷 요청을 하지 않습니다.

import importlib.util
from datetime import date
from pathlib import Path

import sqlite3
from math import isfinite

from fastapi import FastAPI, HTTPException

from price_store import read_prices

root = Path(__file__).resolve().parents[2]

# 다른 폴더의 main.py를 고유한 이름으로 불러옵니다.
source_path = root / "exercises" / "api-day52" / "main.py"
spec = importlib.util.spec_from_file_location(
    "csv_price_api", source_path
)

if spec is None or spec.loader is None:
    raise ImportError("기존 가격 API 코드를 불러올 수 없습니다.")

csv_price_api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(csv_price_api)

# 기존 계산 함수와 거래일 기준을 그대로 재사용합니다.
calculate_price_change = csv_price_api.calculate_price_change
EXPECTED_DATES = csv_price_api.EXPECTED_DATES_2025

# 이번 DB에 실제로 저장한 종목과 기간입니다.
SUPPORTED_CODES = {"005930", "000660"}
DATA_START = date(2025, 1, 2)
DATA_END = date(2025, 6, 30)

app = FastAPI(title="DB 기반 종가 변화율 학습 API")
# 종목·기간을 받아 DB 자료를 검사하고 종가 변화율을 반환합니다.
@app.get("/api/price-change")
def get_price_change(stock_code: str, start_date: date, end_date: date):
    # 요청 형식과 이번 DB의 제공 범위를 확인합니다.
    if len(stock_code) != 6 or not all(
        character in "0123456789" for character in stock_code
    ):
        raise HTTPException(
            status_code=400,
            detail="종목코드는 숫자 0~9로 이루어진 여섯 자리여야 합니다.",
        )

    if stock_code not in SUPPORTED_CODES:
        raise HTTPException(
            status_code=404,
            detail="이 DB에서 조회를 지원하지 않는 종목입니다.",
        )

    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="시작일은 종료일보다 늦을 수 없습니다.",
        )

    if not (DATA_START <= start_date <= end_date <= DATA_END):
        raise HTTPException(
            status_code=400,
            detail="조회 기간은 2025-01-02부터 2025-06-30까지입니다.",
        )

    # CSV 대신 읽기 전용 DB 조회 함수를 호출합니다.
    try:
        rows = read_prices(stock_code, start_date, end_date)
    except (FileNotFoundError, sqlite3.Error):
        raise HTTPException(
            status_code=503,
            detail="가격 DB를 읽을 수 없습니다.",
        )

    # DB에서도 요청 기간의 거래일이 빠지지 않았는지 검사합니다.
    expected_dates = {
        day.isoformat()
        for day in EXPECTED_DATES
        if start_date <= day <= end_date
    }
    actual_dates = {row["date"] for row in rows}
    missing_dates = expected_dates - actual_dates

    if missing_dates:
        raise HTTPException(
            status_code=503,
            detail=(
                "요청 기간에 거래일 자료가 빠져 있습니다: "
                + ", ".join(sorted(missing_dates))
            ),
        )

    if len(actual_dates) < 2:
        raise HTTPException(
            status_code=400,
            detail="종가 변화율 계산에는 서로 다른 거래일이 두 개 이상 필요합니다.",
        )

    # 조회 함수가 날짜순으로 반환한 자료의 양 끝 종가를 검사합니다.
    try:
        first_close = float(rows[0]["close"])
        last_close = float(rows[-1]["close"])
    except (TypeError, ValueError, OverflowError):
        raise HTTPException(
            status_code=503,
            detail="계산에 사용할 종가를 숫자로 읽을 수 없습니다.",
        )

    if not all(
        isfinite(value) and value > 0
        for value in [first_close, last_close]
    ):
        raise HTTPException(
            status_code=503,
            detail="계산에 사용할 종가는 유한한 양수여야 합니다.",
        )

    # 계산식과 응답 항목은 기존 CSV 기반 API와 동일하게 유지합니다.
    change = calculate_price_change(first_close, last_close)

    return {
        "stock_code": stock_code,
        "first_date": rows[0]["date"],
        "last_date": rows[-1]["date"],
        "first_close": first_close,
        "last_close": last_close,
        "price_change": change,
        "price_change_pct": change * 100,
    }

# 직접 실행할 때 준비 상태를 확인합니다.
if __name__ == "__main__":
    assert callable(read_prices)
    assert calculate_price_change(100, 110) > 0
    assert date(2025, 1, 3) in EXPECTED_DATES
    assert date(2025, 1, 4) not in EXPECTED_DATES

    print("DB 조회 함수 연결: 통과")
    print("기존 계산 함수·거래일 기준 불러오기: 통과")

