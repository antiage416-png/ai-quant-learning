# 목적: 종목과 조회 기간을 입력받아 그대로 반환합니다.
# 아직 CSV 조회나 날짜 유효성 검사는 하지 않습니다.
from fastapi import FastAPI, HTTPException
# 파이썬 표준 라이브러리에서 날짜 자료형을 가져옵니다.
from datetime import date
# 파일 경로를 다루는 도구와 CSV를 표로 읽는 도구입니다.
from pathlib import Path
import pandas as pd


app = FastAPI(title="주식 일봉 조회 학습 API")
# 이번 실습 API에서 조회를 지원하는 다섯 종목입니다.
SUPPORTED_STOCK_CODES = {
    "005930",
    "000660",
    "005380",
    "035420",
    "055550",
}
# main.py의 위치를 기준으로 학습 저장소의 최상위 폴더를 찾습니다.
ROOT = Path(__file__).resolve().parents[2]

# 33일차에 저장한 정제 CSV 폴더를 지정합니다.
DATA_DIR = ROOT / "data" / "stock-day33" / "clean"


# GET 요청의 주소와 아래 함수를 연결합니다.
@app.get("/api/prices")
def get_prices(stock_code: str, start_date: date, end_date: date):
    # 받은 입력을 확인할 수 있도록 딕셔너리로 반환합니다.
        # 종목코드가 숫자 0~9로 이루어진 여섯 자리 문자열인지 검사합니다.
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
        # 형식이 올바르더라도 지원 목록에 없는 종목은 거절합니다.
    if stock_code not in SUPPORTED_STOCK_CODES:
        raise HTTPException(
            status_code=404,
            detail="이 API에서 조회를 지원하지 않는 종목입니다.",
        )
    
    # 요청한 종목코드로 CSV 파일 이름을 만듭니다.
    csv_path = DATA_DIR / f"{stock_code}_2025_clean.csv"

    # 지원 종목이라도 실제 파일이 없으면 오류를 응답합니다.
    if not csv_path.is_file():
        raise HTTPException(
            status_code=503,
            detail="조회에 필요한 가격 CSV 파일이 없습니다.",
        )

    # 앞자리 0을 보존하도록 종목코드를 문자열로 읽습니다.
    table = pd.read_csv(csv_path, dtype={"stock_code": str})

    # 읽은 CSV 전체의 데이터 행 수를 반환합니다.
        # CSV의 날짜 문자열을 날짜 자료형으로 변환합니다.
    table["date"] = pd.to_datetime(
        table["date"], format="%Y-%m-%d", errors="raise"
    ).dt.date

    # 시작일과 종료일을 모두 포함하는 행을 선택합니다.
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

