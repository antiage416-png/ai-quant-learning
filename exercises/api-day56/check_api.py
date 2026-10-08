# 목적: 두 종목의 CSV 기반·DB 기반 분석 API 응답을 비교합니다.
# 입력 → 처리 → 결과: 같은 종목·기간 → 두 서버 요청 → 응답 대조.
# 로컬 서버에 조회 요청만 보내며 결과 파일은 저장하지 않습니다.

import json
from math import isclose
from urllib.parse import urlencode
from urllib.request import urlopen


# 지정한 포트의 분석 API에 요청하고 JSON 응답을 읽습니다.
def request_analysis(port, parameters):
    url = (
        f"http://127.0.0.1:{port}/api/price-change?"
        + urlencode(parameters)
    )
    with urlopen(url, timeout=10) as response:
        assert response.status == 200
        return json.load(response)


for stock_code in ["005930", "000660"]:
    parameters = {
        "stock_code": stock_code,
        "start_date": "2025-01-02",
        "end_date": "2025-06-30",
    }

    csv_result = request_analysis(8000, parameters)
    db_result = request_analysis(8001, parameters)

    # 응답 항목과 종목·날짜·종가가 같은지 확인합니다.
    assert csv_result.keys() == db_result.keys()
    assert csv_result["stock_code"] == stock_code

    for key in [
        "stock_code", "first_date", "last_date",
        "first_close", "last_close",
    ]:
        assert csv_result[key] == db_result[key], (
            f"{stock_code}: {key} 값이 다릅니다."
        )

    # 소수 계산의 미세한 오차를 허용해 변화율을 비교합니다.
    for key in ["price_change", "price_change_pct"]:
        assert isclose(
            csv_result[key], db_result[key],
            rel_tol=1e-12, abs_tol=1e-12,
        ), f"{stock_code}: {key} 값이 다릅니다."

    print(f"{stock_code} CSV·DB API 응답 대조: 통과")

print("두 종목 API 응답 대조: 모두 통과")