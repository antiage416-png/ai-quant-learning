# 목적: 두 종목의 종가 변화율을 API로 조회·저장하고 원본과 대조합니다.
# 입력 → 처리 → 결과: 종목·기간 → API 요청·JSON 저장 → 재읽기·원본 대조.
# 로컬 서버에 요청하고 실행마다 새 JSON 파일을 저장합니다.
# 원본 CSV는 읽기만 하며 외부 시세 수집과 실제 주문은 없습니다.

import json
from urllib.parse import urlencode
from urllib.request import urlopen
from pathlib import Path
from uuid import uuid4
from math import isclose

import pandas as pd

# 두 종목의 API 응답을 순서대로 담을 목록입니다.
results = []

# 종목코드만 바꾸고 조회 기간은 동일하게 유지합니다.
for stock_code in ["005930", "000660"]:
    parameters = {
        "stock_code": stock_code,
        "start_date": "2025-01-02",
        "end_date": "2025-06-30",
    }

    url = (
        "http://127.0.0.1:8000/api/price-change?"
        + urlencode(parameters)
    )

    with urlopen(url, timeout=10) as response:
        result = json.load(response)

    results.append(result)

    print("종목코드:", result["stock_code"])
    print("종가 변화율(%):", result["price_change_pct"])

print("조회한 종목 수:", len(results))

# 실행 위치와 관계없이 프로젝트 안의 저장 폴더를 찾습니다.
root = Path(__file__).resolve().parents[2]
output_dir = root / "data" / "stock-day55"
output_dir.mkdir(parents=True, exist_ok=True)

# 매번 다른 이름을 만들어 이전 결과를 보존합니다.
output_path = output_dir / f"price_change_{uuid4()}.json"

# 응답 목록을 새 JSON 파일로 저장합니다.
with output_path.open("x", encoding="utf-8") as file:
    json.dump(results, file, ensure_ascii=False, indent=2)

# 저장한 파일을 다시 읽어 원래 응답 목록과 비교합니다.
with output_path.open("r", encoding="utf-8") as file:
    saved_results = json.load(file)

assert saved_results == results, "저장 전후의 분석 결과가 다릅니다."

print("분석 결과 저장 위치:", output_path)
print("저장 후 다시 읽기 비교: 통과")

# 저장된 결과에 두 종목이 각각 한 번씩 있는지 확인합니다.
assert len(saved_results) == 2
assert {item["stock_code"] for item in saved_results} == {
    "005930", "000660"
}

# API 계산 함수를 호출하지 않고 원본 CSV에서 직접 계산합니다.
for saved in saved_results:
    stock_code = saved["stock_code"]
    csv_path = (
        root / "data" / "stock-day33" / "clean"
        / f"{stock_code}_2025_clean.csv"
    )
    table = pd.read_csv(csv_path, dtype={"stock_code": str})
    table["date"] = pd.to_datetime(
        table["date"], format="%Y-%m-%d", errors="raise"
    )

    # API에 요청했던 기간을 원본에서도 동일하게 선택합니다.
    selected = table.loc[
        table["date"].between("2025-01-02", "2025-06-30")
    ].sort_values("date")

    assert len(selected) >= 2, "대조할 원본 자료가 부족합니다."

    first = selected.iloc[0]
    last = selected.iloc[-1]
    first_close = float(first["close"])
    last_close = float(last["close"])

    # 종가 차이를 첫 종가로 나누어 변화율을 직접 계산합니다.
    expected_change = (last_close - first_close) / first_close

    assert saved["first_date"] == first["date"].strftime("%Y-%m-%d")
    assert saved["last_date"] == last["date"].strftime("%Y-%m-%d")
    assert saved["first_close"] == first_close
    assert saved["last_close"] == last_close
    assert isclose(
        saved["price_change"], expected_change,
        rel_tol=1e-12, abs_tol=1e-12,
    ), f"{stock_code}: 종가 변화율이 다릅니다."
    assert isclose(
        saved["price_change_pct"], expected_change * 100,
        rel_tol=1e-12, abs_tol=1e-12,
    ), f"{stock_code}: 백분율이 다릅니다."

    print(f"{stock_code} 원본 CSV와 저장 결과 대조: 통과")