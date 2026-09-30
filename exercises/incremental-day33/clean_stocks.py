# 목적:
# 완료 상태에 연결된 데이터만 읽어 종목별 CSV 5개를 만듭니다.
#
# 흐름:
# 완료 상태 읽기 → 기존 CSV·월별 원본 읽기 → 자료형 통일
# → 기본 품질 검사 → 종목별 CSV 저장·재읽기
#
# 실행 영향:
# 인터넷 요청, 토큰 발급, 원본·완료 상태 변경은 없습니다.
# data/stock-day33/clean에 CSV를 저장하며 같은 이름이면 덮어씁니다.

import json
import sys
from pathlib import Path

import pandas as pd

from plan_collection import STOCKS


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data/stock-day33"

# 32일차에서 사용한 열 이름과 순서를 그대로 재사용합니다.
sys.path.insert(0, str(ROOT / "exercises/stock-day32"))
from clean_january import FIELD_MAP, NUMBER_COLUMNS, COLUMNS


def build_table(code, info):
    """종목 하나의 기존 CSV와 기록된 원본을 읽어 정리한 표를 반환합니다."""

    parts = []

    # 삼성전자는 기존에 검증한 CSV를 활용합니다.
    # 문자열로 읽어 종목코드의 앞자리 0을 유지합니다.
    if "existing_csv" in info:
        existing = pd.read_csv(
            info["existing_csv"],
            dtype=str,
            keep_default_na=False,
        )
        existing["date"] = pd.to_datetime(
            existing["date"], format="%Y-%m-%d", errors="raise"
        ).astype("datetime64[ns]")
        parts.append(existing[COLUMNS])

    # 폴더의 모든 파일을 무작정 읽지 않고 완료 상태에 등록된 원본만 읽습니다.
    for batch in info["batches"]:
        metadata = json.loads(
            (DATA_DIR / batch["meta_file"]).read_text(encoding="utf-8")
        )

        if metadata["raw_file"] != batch["raw_file"]:
            raise ValueError(f"{code}: 원본 연결이 다릅니다.")

        # 종목·시장·가격 기준과 기록된 요청 기간을 확인합니다.
        expected = {
            "FID_INPUT_ISCD": code,
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "0",
            "FID_INPUT_DATE_1": batch["start_date"].replace("-", ""),
            "FID_INPUT_DATE_2": batch["end_date"].replace("-", ""),
        }
        if any(
            metadata["params"].get(key) != value
            for key, value in expected.items()
        ):
            raise ValueError(f"{code}: 원본 조회 조건이 다릅니다.")

        response = json.loads(
            (DATA_DIR / batch["raw_file"]).read_text(encoding="utf-8")
        )
        if response.get("rt_cd") != "0":
            raise ValueError(f"{code}: 성공한 응답이 아닙니다.")

        original = pd.DataFrame(response["output2"])
        if original.empty or len(original) != batch["count"]:
            raise ValueError(f"{code}: 원본 건수가 완료 기록과 다릅니다.")

        # 필수 API 열을 선택하고 공통 열 이름으로 바꿉니다.
        # 필요한 열이 없으면 오류로 중단됩니다.
        part = original[list(FIELD_MAP)].rename(columns=FIELD_MAP).copy()
        part["stock_code"] = code
        part["market"] = "KRX"
        part["date"] = pd.to_datetime(
            part["date"], format="%Y%m%d", errors="raise"
        ).astype("datetime64[ns]")

        if not part["date"].between(
            pd.Timestamp(batch["start_date"]),
            pd.Timestamp(batch["end_date"]),
        ).all():
            raise ValueError(f"{code}: 요청 범위 밖의 날짜가 있습니다.")

        parts.append(part[COLUMNS])

    if not parts:
        raise ValueError(f"{code}: 변환할 데이터가 없습니다.")

    # 기존 결과와 월별 결과를 세로로 합칩니다.
    # 중복 행은 자동 삭제하지 않고 아래 검사에서 확인합니다.
    table = pd.concat(parts, ignore_index=True)

    for column in ["stock_code", "market"]:
        table[column] = table[column].astype("string")

    for column in NUMBER_COLUMNS:
        values = table[column].replace("", pd.NA)
        table[column] = pd.to_numeric(
            values, errors="raise"
        ).astype("Int64")

    table["date"] = table["date"].astype("datetime64[ns]")
    table = table[COLUMNS].sort_values("date").reset_index(drop=True)

    # 다른 종목이나 시장이 섞이지 않았는지 확인합니다.
    if not (
        table["stock_code"].eq(code).all()
        and table["market"].eq("KRX").all()
    ):
        raise ValueError(f"{code}: 종목 또는 시장이 다릅니다.")

    if table.isna().any().any():
        raise ValueError(f"{code}: 필수값 누락이 있습니다.")

    if table.duplicated(["stock_code", "market", "date"]).any():
        raise ValueError(f"{code}: 날짜 중복이 있습니다.")

    if not table["date"].between("2025-01-01", "2025-12-31").all():
        raise ValueError(f"{code}: 2025년 밖의 날짜가 있습니다.")

    if (table[NUMBER_COLUMNS] < 0).any().any():
        raise ValueError(f"{code}: 가격 또는 거래량에 음수가 있습니다.")

    valid_prices = (
        (table["low"] <= table["high"])
        & table["open"].between(table["low"], table["high"])
        & table["close"].between(table["low"], table["high"])
    )
    if not valid_prices.all():
        raise ValueError(f"{code}: 가격 관계 확인이 필요합니다.")

    return table


def main():
    """5개 종목을 각각 변환하고 CSV 저장 전후를 비교합니다."""

    state = json.loads(
        (DATA_DIR / "state.json").read_text(encoding="utf-8")
    )
    output_dir = DATA_DIR / "clean"
    output_dir.mkdir(parents=True, exist_ok=True)

    # CSV를 다시 읽을 때 사용할 자료형입니다.
    dtypes = {"stock_code": "string", "market": "string"}
    dtypes.update({column: "Int64" for column in NUMBER_COLUMNS})

    total_rows = 0

    for code, name in STOCKS.items():
        info = state["stocks"][code]

        # 이번 변환은 2025년 전체 수집이 끝난 상태를 대상으로 합니다.
        if info["covered_through"] != "2025-12-31":
            raise ValueError(f"{code}: 2025년 조회 완료 상태가 아닙니다.")

        table = build_table(code, info)
        output_path = output_dir / f"{code}_2025_clean.csv"

        table.to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig",
            date_format="%Y-%m-%d",
        )

        # 저장 후 값·열 순서·자료형을 다시 확인합니다.
        saved = pd.read_csv(output_path, dtype=dtypes)
        saved["date"] = pd.to_datetime(
            saved["date"], format="%Y-%m-%d", errors="raise"
        ).astype("datetime64[ns]")
        pd.testing.assert_frame_equal(table, saved)

        first = saved["date"].min().strftime("%Y-%m-%d")
        last = saved["date"].max().strftime("%Y-%m-%d")
        print(f"{code} {name}: {len(saved)}행, {first} ~ {last}, 검사 통과")
        total_rows += len(saved)

    print("\n저장한 종목 수:", len(STOCKS))
    print("전체 행 수:", total_rows)
    print("저장 폴더:", output_dir)
    print("거래일 달력 대조: 아직 하지 않음")


if __name__ == "__main__":
    main()