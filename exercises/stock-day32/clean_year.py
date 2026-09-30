# 목적:
# 완료 목록에 기록된 12개월 원본을 합쳐 연간 CSV로 저장합니다.
#
# 흐름:
# 완료 목록 확인 → 월별 원본·조건 검사 → 합치기
# → 자료형 변환 → 기본 품질 검사 → CSV 저장·재읽기
#
# 실행 영향:
# 인터넷 요청과 원본 변경은 없습니다.
# clean 폴더에 연간 CSV를 저장하며 같은 이름이 있으면 덮어씁니다.

import calendar
import json
from pathlib import Path

import pandas as pd

# 이미 확인한 1월 코드의 열 이름 규칙을 재사용합니다.
# clean_january의 main()은 import만으로 실행되지 않습니다.
from clean_january import FIELD_MAP, NUMBER_COLUMNS, COLUMNS


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data/stock-day32/raw"
CLEAN_DIR = ROOT / "data/stock-day32/clean"


def main():
    """완료된 연간 수집 원본을 변환하고 검증한 CSV를 저장합니다."""

    # 이번 학습에서 만든 연간 수집 폴더 중 가장 최근 폴더를 선택합니다.
    # 최신 실행이 실패했다면 과거 성공 결과로 조용히 대체하지 않습니다.
    run_dirs = sorted(
        path
        for path in RAW_DIR.glob("005930_2025_*")
        if path.is_dir()
    )
    if not run_dirs:
        raise ValueError("연간 수집 폴더가 없습니다.")

    run_dir = run_dirs[-1]
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("최신 실행에 완료 목록이 없습니다.")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if (
        manifest["stock_code"] != "005930"
        or manifest["year"] != 2025
        or manifest["completed_months"] != 12
    ):
        raise ValueError("완료 목록의 종목·연도·월 수가 다릅니다.")

    entries = manifest["files"]

    # 개수만 12개인 것이 아니라 1~12월이 각각 있는지 확인합니다.
    months = sorted(item["month"] for item in entries)
    if months != list(range(1, 13)):
        raise ValueError("월 누락 또는 중복이 있습니다.")

    frames = []

    for item in sorted(entries, key=lambda entry: entry["month"]):
        month = item["month"]
        last_day = calendar.monthrange(2025, month)[1]
        start = f"2025{month:02d}01"
        end = f"2025{month:02d}{last_day:02d}"

        metadata = json.loads(
            (run_dir / item["meta_file"]).read_text(encoding="utf-8")
        )

        # 원본과 조회 조건 파일이 같은 데이터를 가리키는지 확인합니다.
        if metadata["raw_file"] != item["raw_file"]:
            raise ValueError(f"{month}월 원본 연결이 다릅니다.")

        expected = {
            "FID_INPUT_ISCD": "005930",
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_DATE_1": start,
            "FID_INPUT_DATE_2": end,
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "0",
        }
        if any(
            metadata["params"].get(key) != value
            for key, value in expected.items()
        ):
            raise ValueError(f"{month}월 조회 조건이 다릅니다.")

        response = json.loads(
            (run_dir / item["raw_file"]).read_text(encoding="utf-8")
        )
        if response.get("rt_cd") != "0":
            raise ValueError(f"{month}월 API 응답이 성공 상태가 아닙니다.")

        original = pd.DataFrame(response["output2"])
        if original.empty or len(original) != item["response_count"]:
            raise ValueError(f"{month}월 응답 건수가 완료 목록과 다릅니다.")

        missing = set(FIELD_MAP) - set(original.columns)
        if missing:
            raise ValueError(f"{month}월 필수 필드 누락: {sorted(missing)}")

        # 필요한 열을 선택하고 공통 이름으로 바꿉니다.
        part = original[list(FIELD_MAP)].rename(columns=FIELD_MAP).copy()
        part["date"] = pd.to_datetime(
            part["date"], format="%Y%m%d", errors="raise"
        ).astype("datetime64[ns]")

        # 연도뿐 아니라 각 월의 요청 범위 안에 있는지 검사합니다.
        start_day = pd.to_datetime(start, format="%Y%m%d")
        end_day = pd.to_datetime(end, format="%Y%m%d")
        if not part["date"].between(start_day, end_day).all():
            raise ValueError(f"{month}월 요청 범위 밖의 날짜가 있습니다.")

        frames.append(part)

    # 월별 표를 세로로 연결하고 새 행 번호를 부여합니다.
    table = pd.concat(frames, ignore_index=True)

    table["stock_code"] = "005930"
    table["market"] = "KRX"
    for column in ["stock_code", "market"]:
        table[column] = table[column].astype("string")

    for column in NUMBER_COLUMNS:
        values = table[column].replace("", pd.NA)
        table[column] = pd.to_numeric(
            values, errors="raise"
        ).astype("Int64")

    table = table[COLUMNS].sort_values("date").reset_index(drop=True)

    # 잘못된 행을 삭제하거나 누락값을 채우지 않고 원인 확인을 위해 멈춥니다.
    if table.isna().any().any():
        raise ValueError("필수값 누락이 있습니다.")

    if table.duplicated(["stock_code", "market", "date"]).any():
        raise ValueError("동일 종목·시장·거래일 중복이 있습니다.")

    if (table[NUMBER_COLUMNS] < 0).any().any():
        raise ValueError("가격 또는 거래량에 음수가 있습니다.")

    valid_prices = (
        (table["low"] <= table["high"])
        & table["open"].between(table["low"], table["high"])
        & table["close"].between(table["low"], table["high"])
    )
    if not valid_prices.all():
        raise ValueError("시가·종가·고가·저가 관계 확인이 필요합니다.")

    expected_count = sum(item["response_count"] for item in entries)
    if len(table) != expected_count:
        raise ValueError("합친 행 수가 월별 응답 합계와 다릅니다.")

    # 수집 폴더 이름을 결과 파일명에 사용해 원본 실행과 연결합니다.
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CLEAN_DIR / f"{run_dir.name}_clean.csv"
    table.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%d",
    )

    # CSV를 다시 읽을 때 문자열·정수·날짜 자료형을 복원합니다.
    dtypes = {"stock_code": "string", "market": "string"}
    dtypes.update({column: "Int64" for column in NUMBER_COLUMNS})

    saved = pd.read_csv(output_path, dtype=dtypes)
    saved["date"] = pd.to_datetime(
        saved["date"], format="%Y-%m-%d", errors="raise"
    ).astype("datetime64[ns]")

    pd.testing.assert_frame_equal(table, saved)

    print("사용한 원본 폴더:", run_dir.name)
    print("확인한 월 수:", len(entries))
    print("연간 행·열:", saved.shape)
    print(
        "날짜 범위:",
        saved["date"].min().strftime("%Y-%m-%d"),
        "~",
        saved["date"].max().strftime("%Y-%m-%d"),
    )
    print("월별 조건·기본 품질 검사: 통과")
    print("CSV 재읽기 비교: 통과")
    print("거래일 달력 대조: 아직 하지 않음")
    print("저장 위치:", output_path)


if __name__ == "__main__":
    main()