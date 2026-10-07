# 목적: 종목·기간을 검사하고 저장된 2025년 일봉 CSV를 조회합니다.
# 입력 → 처리 → 결과: 종목·기간 → 자료 검사·행 선택 → JSON 응답.
# 원본 파일 수정과 외부 데이터 요청은 없습니다.
# 종가가 무한대나 결측값이 아닌 유한한 숫자인지 확인합니다.
from math import isfinite
from datetime import date
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException


app = FastAPI(title="주식 일봉 조회 학습 API")

# 이번 실습에서 조회를 지원하는 종목입니다.
SUPPORTED_STOCK_CODES = {
    "005930",
    "000660",
    "005380",
    "035420",
    "055550",
}

# 현재 파일을 기준으로 학습 저장소와 가격 자료 폴더를 찾습니다.
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "stock-day33" / "clean"

# 34일차에서 사용한 2025년 휴장일 목록입니다.
HOLIDAYS_2025 = {
    "2025-01-01", "2025-01-27", "2025-01-28", "2025-01-29",
    "2025-01-30", "2025-03-03", "2025-05-01", "2025-05-05",
    "2025-05-06", "2025-06-03", "2025-06-06", "2025-08-15",
    "2025-10-03", "2025-10-06", "2025-10-07", "2025-10-08",
    "2025-10-09", "2025-12-25", "2025-12-31",
}

# 평일에서 기존 휴장일을 제외해 기준 거래일을 만듭니다.
EXPECTED_DATES_2025 = {
    day.date()
    for day in pd.bdate_range("2025-01-01", "2025-12-31")
    if day.strftime("%Y-%m-%d") not in HOLIDAYS_2025
}


# 종목·기간을 받아 자료를 검사하고 해당 기간의 가격을 반환합니다.
@app.get("/api/prices")
def get_prices(stock_code: str, start_date: date, end_date: date):
    # 종목코드는 숫자 0~9로 이루어진 여섯 자리 문자열이어야 합니다.
    if len(stock_code) != 6 or not all(
        character in "0123456789" for character in stock_code
    ):
        raise HTTPException(
            status_code=400,
            detail="종목코드는 숫자 0~9로 이루어진 여섯 자리여야 합니다.",
        )

    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="시작일은 종료일보다 늦을 수 없습니다.",
        )

    # 현재 자료가 제공하는 연도 안에서만 조회합니다.
    if start_date.year != 2025 or end_date.year != 2025:
        raise HTTPException(
            status_code=400,
            detail="조회 기간은 2025년 안에서 지정해야 합니다.",
        )

    if stock_code not in SUPPORTED_STOCK_CODES:
        raise HTTPException(
            status_code=404,
            detail="이 API에서 조회를 지원하지 않는 종목입니다.",
        )

    csv_path = DATA_DIR / f"{stock_code}_2025_clean.csv"

    if not csv_path.is_file():
        raise HTTPException(
            status_code=503,
            detail="조회에 필요한 가격 CSV 파일이 없습니다.",
        )

    # 종목코드의 앞자리 0을 보존하며 CSV를 읽습니다.
    try:
        table = pd.read_csv(csv_path, dtype={"stock_code": str})
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=503,
            detail="가격 CSV가 비어 있어 조회할 수 없습니다.",
        )

    if table.empty:
        raise HTTPException(
            status_code=503,
            detail="가격 CSV에 데이터 행이 없습니다.",
        )

    # 응답 구성에 필요한 열이 모두 있는지 확인합니다.
    required_columns = {
        "stock_code", "market", "date",
        "open", "high", "low", "close", "volume",
    }
    missing_columns = required_columns - set(table.columns)

    if missing_columns:
        raise HTTPException(
            status_code=503,
            detail=(
                "가격 CSV에 필수 열이 없습니다: "
                + ", ".join(sorted(missing_columns))
            ),
        )

    # CSV의 날짜를 비교 가능한 날짜 자료형으로 바꿉니다.
    try:
        table["date"] = pd.to_datetime(
            table["date"], format="%Y-%m-%d", errors="raise"
        ).dt.date
    except ValueError:
        raise HTTPException(
            status_code=503,
            detail="가격 CSV에 올바르지 않은 날짜가 있습니다.",
        )

    if table["date"].isna().any():
        raise HTTPException(
            status_code=503,
            detail="가격 CSV에 날짜가 빠진 행이 있습니다.",
        )

    # 요청 기간에 있어야 하는 거래일과 실제 자료를 대조합니다.
    expected_dates = {
        day for day in EXPECTED_DATES_2025
        if start_date <= day <= end_date
    }
    missing_dates = expected_dates - set(table["date"])

    if missing_dates:
        raise HTTPException(
            status_code=503,
            detail=(
                "요청 기간에 거래일 자료가 빠져 있습니다: "
                + ", ".join(day.isoformat() for day in sorted(missing_dates))
            ),
        )

    # 시작일과 종료일을 모두 포함해 선택합니다.
    selected = table.loc[
        (table["date"] >= start_date)
        & (table["date"] <= end_date)
    ]

    return {
        "stock_code": stock_code,
        "start_date": start_date,
        "end_date": end_date,
        "source_rows": len(table),
        "selected_rows": len(selected),
        "prices": selected.to_dict(orient="records"),
    }

# 첫 종가와 마지막 종가를 받아 기간 종가 변화율을 계산합니다.
def calculate_price_change(first_close, last_close):
    return last_close / first_close - 1

# 종목·기간을 받아 첫 거래일 종가 대비 마지막 종가 변화율을 반환합니다.
@app.get("/api/price-change")
def get_price_change(stock_code: str, start_date: date, end_date: date):
    # 기존 조회 함수의 입력·자료 검사를 먼저 거칩니다.
    quoted = get_prices(stock_code, start_date, end_date)
    rows = sorted(quoted["prices"], key=lambda row: row["date"])

    # 서로 다른 두 거래일 이상이 있어야 기간 변화를 비교할 수 있습니다.
    if len({row["date"] for row in rows}) < 2:
        raise HTTPException(
            status_code=400,
            detail="종가 변화율 계산에는 서로 다른 거래일이 두 개 이상 필요합니다.",
        )

    # 계산에 사용할 양 끝의 종가를 숫자로 변환합니다.
    try:
        first_close = float(rows[0]["close"])
        last_close = float(rows[-1]["close"])
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=503,
            detail="계산에 사용할 종가를 숫자로 읽을 수 없습니다.",
        )

    if not all(isfinite(value) and value > 0 for value in [first_close, last_close]):
        raise HTTPException(
            status_code=503,
            detail="계산에 사용할 종가는 유한한 양수여야 합니다.",
        )

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