# 목적:
# 5개 종목에서 아직 조회하지 않은 기간만 월별로 수집합니다.
#
# 흐름:
# 완료 상태 읽기 → 다음 날짜 계산 → 월별 조회
# → 원본·조건 저장 → 완료 날짜 갱신
#
# 실행 영향:
# 최초 정상 실행에서는 삼성전자를 제외한 시세 요청 48회가 예정됩니다.
# 요청 전 1초 대기하며, 필요하면 인증 요청이 추가됩니다.
# data/stock-day33에 원본과 완료 상태를 저장합니다.
# 키·토큰은 출력하지 않으며 주문은 하지 않습니다.

import calendar
import json
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# 같은 폴더의 종목 목록과 기존 삼성전자 검증 함수를 재사용합니다.
from plan_collection import STOCKS, check_existing_samsung


ROOT = Path(__file__).resolve().parents[2]

# 하이픈이 들어간 폴더를 직접 import할 수 없으므로
# Python이 모듈을 찾는 경로에 기존 코드 폴더를 추가합니다.
sys.path.insert(0, str(ROOT / "exercises/stock-day32"))
from kis_auth import get_access_token

DATA_DIR = ROOT / "data/stock-day33"
STATE_PATH = DATA_DIR / "state.json"
BASE_URL = "https://openapi.koreainvestment.com:9443"
API_PATH = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"

START_DATE = date(2025, 1, 1)
END_DATE = date(2025, 12, 31)

# 가격·시장 기준이 다른 수집 상태를 섞지 않도록 기록합니다.
CONDITIONS = {
    "provider": "한국투자증권",
    "market": "KRX",
    "period": "D",
    "adjusted": True,
    "start_date": START_DATE.isoformat(),
}


def save_state(state):
    """완료 상태를 임시 파일에 쓴 뒤 최종 파일로 교체합니다."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary = STATE_PATH.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 저장 도중 중단되어 기존 상태 파일이 반만 기록되는 것을 줄입니다.
    temporary.replace(STATE_PATH)


def load_state():
    """기존 상태를 읽거나 검증된 삼성전자 결과로 초기 상태를 만듭니다."""

    if STATE_PATH.is_file():
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))

        if state["conditions"] != CONDITIONS:
            raise ValueError("저장된 수집 조건이 현재 설정과 다릅니다.")
    else:
        csv_path, covered_through = check_existing_samsung()
        state = {
            "conditions": CONDITIONS,
            "stocks": {
                "005930": {
                    "covered_through": covered_through,
                    "existing_csv": str(csv_path),
                    "batches": [],
                }
            },
        }
        save_state(state)

    # 완료 기록만 남고 실제 파일이 사라진 상태로 건너뛰지 않게 합니다.
    for info in state["stocks"].values():
        if "existing_csv" in info:
            if not Path(info["existing_csv"]).is_file():
                raise ValueError("기존 삼성전자 CSV가 없습니다.")

        for batch in info["batches"]:
            for field in ["raw_file", "meta_file"]:
                if not (DATA_DIR / batch[field]).is_file():
                    raise ValueError("완료 기록에 연결된 파일이 없습니다.")

    return state


def fetch_month(code, start, end, token):
    """기간 하나를 조회하고 원본·조건을 저장한 뒤 파일 정보를 반환합니다."""

    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code,
        "FID_INPUT_DATE_1": start.strftime("%Y%m%d"),
        "FID_INPUT_DATE_2": end.strftime("%Y%m%d"),
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

    # 각 시세 요청 전에 대기합니다. 자동 재시도는 하지 않습니다.
    time.sleep(1)
    with urlopen(request, timeout=20) as response:
        raw_body = response.read()

    collected_at = datetime.now(timezone.utc)
    result = json.loads(raw_body.decode("utf-8"))
    if result.get("rt_cd") != "0":
        raise ValueError("API 업무 처리 실패")

    records = result.get("output2")
    if not isinstance(records, list) or not records:
        # 이번 5개 종목의 월별 수집에서는 빈 응답을 자동 완료 처리하지 않습니다.
        raise ValueError("시세 목록이 비어 있어 확인이 필요합니다.")

    # 완료 날짜를 갱신하기 전에 응답 날짜의 기본 조건을 검사합니다.
    dates = [
        datetime.strptime(row["stck_bsop_date"], "%Y%m%d").date()
        for row in records
    ]
    if any(day < start or day > end for day in dates):
        raise ValueError("요청 범위 밖의 날짜가 있습니다.")
    if len(dates) != len(set(dates)):
        raise ValueError("응답에 날짜 중복이 있습니다.")

    # 실행 시각을 넣어 중단 후 다시 받아도 기존 원본을 덮어쓰지 않습니다.
    stamp = collected_at.strftime("%Y%m%dT%H%M%S%fZ")
    stem = f"{code}_{start:%Y%m%d}_{end:%Y%m%d}_{stamp}"
    raw_relative = Path("raw") / code / f"{stem}.json"
    meta_relative = Path("raw") / code / f"{stem}_meta.json"

    raw_path = DATA_DIR / raw_relative
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(raw_body)

    metadata = {
        "provider": "한국투자증권",
        "endpoint": BASE_URL + API_PATH,
        "params": params,
        "collected_at": collected_at.isoformat(),
        "raw_file": raw_relative.as_posix(),
    }
    (DATA_DIR / meta_relative).write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 인증정보가 없는 저장 결과만 호출한 곳으로 돌려줍니다.
    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "count": len(records),
        "raw_file": raw_relative.as_posix(),
        "meta_file": meta_relative.as_posix(),
    }


def main():
    """종목별 완료 날짜 다음부터 목표 종료일까지 수집합니다."""

    state = load_state()
    token = None
    completed_requests = 0
    skipped_stocks = 0

    for code, name in STOCKS.items():
        info = state["stocks"].get(code)

        if info is None:
            info = {"covered_through": None, "batches": []}
            state["stocks"][code] = info

        # 아직 수집하지 않은 종목은 시작일부터,
        # 기존 종목은 조회 완료 날짜의 다음 날부터 진행합니다.
        if info["covered_through"] is None:
            next_date = START_DATE
        else:
            next_date = (
                date.fromisoformat(info["covered_through"])
                + timedelta(days=1)
            )

        if next_date > END_DATE:
            print(f"{code} {name}: 완료 범위, 건너뛰기")
            skipped_stocks += 1
            continue

        while next_date <= END_DATE:
            last_day = calendar.monthrange(
                next_date.year, next_date.month
            )[1]

            # 해당 월 말일과 목표 종료일 중 더 이른 날까지만 요청합니다.
            month_end = date(next_date.year, next_date.month, last_day)
            request_end = min(month_end, END_DATE)

            # 실제 수집할 것이 있을 때만 인증 함수를 호출합니다.
            # 모두 완료됐다면 토큰을 읽거나 발급하지 않습니다.
            if token is None:
                token = get_access_token()

            print(f"{code} {name}: {next_date} ~ {request_end} 조회")
            batch = fetch_month(code, next_date, request_end, token)

            # 원본과 조건 파일 저장이 성공한 뒤에만 완료 상태를 갱신합니다.
            info["batches"].append(batch)
            info["covered_through"] = request_end.isoformat()
            save_state(state)

            completed_requests += 1
            print(f"저장 및 완료 상태 기록: {batch['count']}건")

            next_date = request_end + timedelta(days=1)

    print("\n이번 실행에서 완료한 시세 요청:", completed_requests)
    print("전체 범위를 건너뛴 종목:", skipped_stocks)
    print("완료 상태 파일:", STATE_PATH)


if __name__ == "__main__":
    try:
        main()
    except HTTPError as error:
        status = error.code
        error.close()
        raise SystemExit(
            f"수집 중단: HTTP {status}. 저장 완료된 범위는 유지됩니다."
        ) from None
    except (URLError, TimeoutError):
        raise SystemExit(
            "수집 중단: 연결 또는 응답 시간 초과."
        ) from None
    except (ValueError, KeyError, TypeError, AttributeError, OSError):
        raise SystemExit(
            "수집 중단: 설정·응답·저장 상태 확인이 필요합니다."
        ) from None

    