# 목적:
# 기존 삼성전자 수집 기록을 확인하고 5개 종목의 수집 계획을 계산합니다.
#
# 흐름:
# 기존 CSV 찾기 → 연결된 완료 목록·조회 조건 확인 → 종목별 계획 출력
#
# 실행 영향:
# 로컬 파일을 읽기만 합니다.
# API 요청, 토큰 발급, 파일 저장은 없습니다.
# 이 단계는 최초 계획 확인이며 증분 수집기 전체가 완성된 것은 아닙니다.

import calendar
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

# 종목코드는 앞자리 0을 보존하는 문자열로 유지합니다.
STOCKS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "005380": "현대차",
    "035420": "NAVER",
    "055550": "신한지주",
}


def check_existing_samsung():
    """기존 연간 CSV와 연결된 12개월 조회 완료 기록을 확인합니다."""

    clean_dir = ROOT / "data/stock-day32/clean"
    files = sorted(clean_dir.glob("005930_2025_*_clean.csv"))

    if not files:
        raise ValueError("확인했던 삼성전자 연간 CSV를 찾지 못했습니다.")

    csv_path = files[-1]

    # CSV 이름에서 _clean.csv를 빼면 연결된 원본 폴더 이름입니다.
    # 수정 시각이 비슷한 다른 원본을 임의로 선택하지 않습니다.
    run_name = csv_path.name.removesuffix("_clean.csv")
    run_dir = ROOT / "data/stock-day32/raw" / run_name

    manifest = json.loads(
        (run_dir / "manifest.json").read_text(encoding="utf-8")
    )

    if (
        manifest["stock_code"] != "005930"
        or manifest["year"] != 2025
        or manifest["completed_months"] != 12
    ):
        raise ValueError("기존 완료 목록의 종목·연도·월 수가 다릅니다.")

    entries = manifest["files"]

    # 1~12월이 각각 한 번씩 기록돼 있는지 확인합니다.
    months = sorted(item["month"] for item in entries)
    if months != list(range(1, 13)):
        raise ValueError("기존 완료 목록에 월 누락 또는 중복이 있습니다.")

    for item in entries:
        month = item["month"]
        last_day = calendar.monthrange(2025, month)[1]

        metadata = json.loads(
            (run_dir / item["meta_file"]).read_text(encoding="utf-8")
        )

        # 종목·시장·기간·수정주가 조건이 이번 계획과 같은지 확인합니다.
        expected = {
            "FID_INPUT_ISCD": "005930",
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_DATE_1": f"2025{month:02d}01",
            "FID_INPUT_DATE_2": f"2025{month:02d}{last_day:02d}",
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "0",
        }
        if any(
            metadata["params"].get(key) != value
            for key, value in expected.items()
        ):
            raise ValueError(f"{month}월의 기존 조회 조건이 다릅니다.")

        # 조회 조건 파일과 완료 목록이 같은 원본을 가리키는지 확인합니다.
        if metadata["raw_file"] != item["raw_file"]:
            raise ValueError(f"{month}월 원본 연결이 다릅니다.")

        if not (run_dir / item["raw_file"]).is_file():
            raise ValueError(f"{month}월 원본 파일이 없습니다.")

    # 반환값은 실제 마지막 거래일이 아니라 확인한 조회 범위의 끝입니다.
    return csv_path, "2025-12-31"


def main():
    """확인된 기존 결과를 활용해 최초 수집 계획만 출력합니다."""

    csv_path, covered_through = check_existing_samsung()
    print("활용할 기존 CSV:", csv_path.name)
    print("삼성전자 조회 완료 범위: 2025-01-01 ~", covered_through)
    print()

    planned_requests = 0

    for code, name in STOCKS.items():
        if code == "005930":
            print(f"{code} {name}: 기존 결과 활용, 추가 요청 0회")
        else:
            print(f"{code} {name}: 2025년 1~12월 수집 예정, 요청 12회")
            planned_requests += 12

    print("\n예정 시세 요청 합계:", planned_requests)
    print("실제 API 요청: 실행하지 않음")


if __name__ == "__main__":
    main()