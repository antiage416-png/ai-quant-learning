# 목적:
# 삼성전자의 2025년 1월 KRX 일별 수정주가를 요청하고 원본을 저장합니다.
#
# 흐름:
# 토큰 준비 → 조회 요청 → 성공 여부 확인 → 원본·조회 조건 저장
#
# 실행 영향:
# 시세 조회 요청 1회를 보냅니다.
# 토큰이 만료됐다면 인증 요청도 1회 발생합니다.
# data/stock-day32/raw에 응답 JSON과 조회 조건 JSON을 저장합니다.
# 키·토큰은 출력하거나 시세 파일에 저장하지 않습니다. 주문은 없습니다.

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# 같은 폴더에 만든 인증 함수를 가져옵니다.
# import만으로는 인증 요청이 발생하지 않습니다.
from kis_auth import get_access_token


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data/stock-day32/raw"
BASE_URL = "https://openapi.koreainvestment.com:9443"
API_PATH = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"


def main():
    """1월 시세를 조회·저장하고 건수와 응답 날짜 범위를 출력합니다."""

    # 이 함수는 .env를 읽고 유효한 토큰을 반환합니다.
    # 따라서 호출 후 환경변수에서 앱키·앱시크릿도 읽을 수 있습니다.
    token = get_access_token()

    # 조회 조건입니다. 인증정보와 분리해 나중에 함께 기록합니다.
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",  # KRX 시장
        "FID_INPUT_ISCD": "005930",     # 삼성전자 종목코드
        "FID_INPUT_DATE_1": "20250101", # 조회 시작일
        "FID_INPUT_DATE_2": "20250131", # 조회 종료일
        "FID_PERIOD_DIV_CODE": "D",    # 일별 데이터
        "FID_ORG_ADJ_PRC": "0",        # 수정주가
    }

    # urlencode는 사전을 URL의 조회 조건 문자열로 바꿉니다.
    # 앱키·앱시크릿·토큰은 URL에 넣지 않고 요청 헤더로 전달합니다.
    request = Request(
        url=BASE_URL + API_PATH + "?" + urlencode(params),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "authorization": f"Bearer {token}",
            "appkey": os.environ["KIS_APP_KEY"],
            "appsecret": os.environ["KIS_APP_SECRET"],
            "tr_id": "FHKST03010100",  # 사용할 조회 기능의 거래 ID
            "custtype": "P",          # 개인 고객
        },
        method="GET",
    )

    # 응답 본문을 바이트로 보관해 가공 전 내용을 그대로 저장합니다.
    # 실패 시 자동 재시도하지 않습니다.
    with urlopen(request, timeout=20) as response:
        raw_body = response.read()

    collected_at = datetime.now(timezone.utc)

    # JSON을 Python 사전으로 변환해 API 처리 결과를 확인합니다.
    result = json.loads(raw_body.decode("utf-8"))

    # HTTP 요청 성공과 API 업무 처리 성공은 따로 확인해야 합니다.
    # 이 API의 rt_cd가 "0"이면 정상 처리입니다.
    if result.get("rt_cd") != "0":
        raise ValueError("API 업무 처리 실패")

    # 날짜별 시세 목록은 output2에 들어 있습니다.
    records = result.get("output2")
    if not isinstance(records, list) or not records:
        raise ValueError("날짜별 시세 목록 없음")

    # 실행 시각을 파일명에 넣어 이전 응답과 구분합니다.
    # UTC는 기준 시간대이며 실제 수집 시각도 함께 기록합니다.
    stamp = collected_at.strftime("%Y%m%dT%H%M%S%fZ")
    stem = f"005930_202501_{stamp}"

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / f"{stem}.json"
    meta_path = RAW_DIR / f"{stem}_meta.json"

    # 응답 본문은 변환하지 않은 바이트 그대로 저장합니다.
    raw_path.write_bytes(raw_body)

    # 재현에 필요한 조회 조건을 별도 파일로 저장합니다.
    # 인증 헤더는 포함하지 않습니다.
    metadata = {
        "provider": "한국투자증권",
        "endpoint": BASE_URL + API_PATH,
        "params": params,
        "collected_at": collected_at.isoformat(),
        "raw_file": raw_path.name,
    }
    meta_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 유효한 날짜가 있는 행만 골라 응답 범위를 표시합니다.
    # 원본 파일에서는 어떤 행도 삭제하지 않습니다.
    dates = [
        row["stck_bsop_date"]
        for row in records
        if isinstance(row, dict) and row.get("stck_bsop_date")
    ]
    if not dates:
        raise ValueError("응답 날짜 확인 불가")

    print("조회 결과: 성공")
    print("응답 목록 건수:", len(records))
    print("날짜가 있는 행 수:", len(dates))
    print("응답 날짜 범위:", min(dates), "~", max(dates))
    print("원본 저장:", raw_path)
    print("조회 조건 저장:", meta_path)


# 직접 실행할 때만 조회합니다.
if __name__ == "__main__":
    try:
        main()
    except HTTPError as error:
        status = error.code
        error.close()
        raise SystemExit(f"요청 실패: HTTP {status}") from None
    except (URLError, TimeoutError):
        raise SystemExit("요청 실패: 연결 또는 응답 시간 초과") from None
    except (ValueError, KeyError, TypeError, AttributeError, OSError):
        # 인증정보가 섞이지 않도록 예외 원문이나 헤더를 출력하지 않습니다.
        raise SystemExit(
            "처리 실패: 설정·API 응답·저장 상태 확인이 필요합니다."
        ) from None