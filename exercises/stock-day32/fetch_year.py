# 목적:
# 삼성전자 2025년 일별 수정주가를 한 달씩 조회해 원본으로 저장합니다.
#
# 흐름:
# 토큰 준비 → 월별 날짜 계산 → 요청 → 원본·조회 조건 저장
#
# 실행 영향:
# 정상 완료 시 시세 요청 총 12회, 요청 사이 1초 대기.
# 토큰이 만료됐다면 인증 요청도 발생할 수 있습니다.
# 실행별 새 폴더에 저장하며 기존 1월 실습 파일은 변경하지 않습니다.
# 실패하면 즉시 중단하고 이미 저장한 파일은 유지합니다.
# 키·토큰은 출력하거나 시세 파일에 저장하지 않습니다.

import calendar  # 각 달의 마지막 날짜를 구합니다.
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from kis_auth import get_access_token


ROOT = Path(__file__).resolve().parents[2]
BASE_URL = "https://openapi.koreainvestment.com:9443"
API_PATH = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"


def main():
    """2025년 12개월의 응답을 각각 저장하고 완료 목록을 남깁니다."""

    token = get_access_token()

    # 실행마다 별도 폴더를 만들어 서로 다른 수집 결과가 섞이지 않게 합니다.
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = ROOT / "data/stock-day32/raw" / f"005930_2025_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=False)

    # 완료된 월의 파일명과 건수를 모읍니다.
    completed = []

    # range(1, 13)은 1부터 12까지 반복합니다.
    for month in range(1, 13):
        # 두 번째 요청부터 대기합니다.
        # 응답 처리가 끝난 뒤 1초 쉬고 다음 요청을 보냅니다.
        if month > 1:
            time.sleep(1)

        # monthrange는 (첫날의 요일, 그 달의 일수)를 반환합니다.
        # [1]을 선택하면 해당 월의 마지막 날짜를 얻습니다.
        last_day = calendar.monthrange(2025, month)[1]

        # :02d는 정수를 두 자리로 표시합니다. 예: 1 → 01
        start_date = f"2025{month:02d}01"
        end_date = f"2025{month:02d}{last_day:02d}"

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": "005930",
            "FID_INPUT_DATE_1": start_date,
            "FID_INPUT_DATE_2": end_date,
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "0",
        }

        request = Request(
            url=BASE_URL + API_PATH + "?" + urlencode(params),
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "authorization": f"Bearer {token}",
                "appkey": os.environ["KIS_APP_KEY"],
                "appsecret": os.environ["KIS_APP_SECRET"],
                "tr_id": "FHKST03010100",
                "custtype": "P",
            },
            method="GET",
        )

        print(f"{month:02d}월 조회 시작")

        # 월별로 한 번 요청하며 자동 재시도는 하지 않습니다.
        with urlopen(request, timeout=20) as response:
            raw_body = response.read()

        collected_at = datetime.now(timezone.utc).isoformat()
        result = json.loads(raw_body.decode("utf-8"))

        if result.get("rt_cd") != "0":
            raise ValueError("API 업무 처리 실패")

        records = result.get("output2")
        if not isinstance(records, list) or not records:
            raise ValueError("시세 목록 없음")

        # 원본 응답 본문을 그대로 저장합니다.
        raw_name = f"005930_2025{month:02d}.json"
        (run_dir / raw_name).write_bytes(raw_body)

        # 인증정보를 제외한 조회 조건과 수집 시각을 기록합니다.
        metadata = {
            "provider": "한국투자증권",
            "endpoint": BASE_URL + API_PATH,
            "params": params,
            "collected_at": collected_at,
            "raw_file": raw_name,
        }
        meta_path = run_dir / f"005930_2025{month:02d}_meta.json"
        meta_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        completed.append({
            "month": month,
            "raw_file": raw_name,
            "meta_file": meta_path.name,
            "response_count": len(records),
        })
        print(f"{month:02d}월 저장 완료: 응답 {len(records)}건")

    # 이 파일은 12개월 수집이 모두 성공한 경우에만 생성합니다.
    # 다음 변환 단계에서는 이 목록에 기록된 원본만 사용합니다.
    manifest = {
        "stock_code": "005930",
        "year": 2025,
        "completed_months": len(completed),
        "files": completed,
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 이것은 응답 건수의 합이며 거래일 완전성을 검증한 수치는 아닙니다.
    total = sum(item["response_count"] for item in completed)
    print("\n완료한 월:", len(completed))
    print("월별 응답 건수 합계:", total)
    print("원본 저장 폴더:", run_dir)
    print("완료 목록: manifest.json")


if __name__ == "__main__":
    try:
        main()
    except HTTPError as error:
        status = error.code
        error.close()
        raise SystemExit(
            f"수집 중단: HTTP {status}. 저장된 월별 파일은 유지됩니다."
        ) from None
    except (URLError, TimeoutError):
        raise SystemExit(
            "수집 중단: 연결 또는 응답 시간 초과. 저장된 파일은 유지됩니다."
        ) from None
    except (ValueError, KeyError, TypeError, AttributeError, OSError):
        raise SystemExit(
            "수집 중단: 설정·응답·파일 확인이 필요합니다. 저장된 파일은 유지됩니다."
        ) from None