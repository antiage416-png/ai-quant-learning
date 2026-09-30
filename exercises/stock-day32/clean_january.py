# 목적:
# 저장된 삼성전자 1월 응답을 공통 8개 열로 정리하고 CSV로 저장합니다.
#
# 흐름:
# 조회 조건 읽기 → 연결된 원본 읽기 → 열·자료형 변환
# → 기본 검사 → CSV 저장 → 다시 읽어 비교
#
# 실행 영향:
# 인터넷 요청은 없습니다. 원본과 인증정보는 변경하지 않습니다.
# clean 폴더에 CSV를 저장하며 같은 이름이 있으면 덮어씁니다.

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data/stock-day32/raw"
CLEAN_DIR = ROOT / "data/stock-day32/clean"

# 실제 API 필드 이름을 우리가 정한 열 이름으로 연결합니다.
FIELD_MAP = {
    "stck_bsop_date": "date",
    "stck_oprc": "open",
    "stck_hgpr": "high",
    "stck_lwpr": "low",
    "stck_clpr": "close",
    "acml_vol": "volume",
}

NUMBER_COLUMNS = ["open", "high", "low", "close", "volume"]
COLUMNS = [
    "stock_code", "market", "date",
    "open", "high", "low", "close", "volume",
]


def main():
    """최신 1월 응답을 변환하고 검증한 뒤 CSV로 저장합니다."""

    # glob은 이름 패턴과 일치하는 파일을 찾습니다.
    # 파일명에 UTC 시각이 들어 있으므로 정렬한 마지막 파일을 선택합니다.
    meta_files = sorted(RAW_DIR.glob("005930_202501_*_meta.json"))
    if not meta_files:
        raise ValueError("먼저 1월 시세 조회를 실행하세요.")

    meta_path = meta_files[-1]
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    params = metadata["params"]

    # 다른 조건의 데이터를 실수로 같은 결과에 넣지 않도록 확인합니다.
    expected = {
        "FID_INPUT_ISCD": "005930",
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_DATE_1": "20250101",
        "FID_INPUT_DATE_2": "20250131",
        "FID_PERIOD_DIV_CODE": "D",
        "FID_ORG_ADJ_PRC": "0",
    }
    if any(params.get(key) != value for key, value in expected.items()):
        raise ValueError("조회 조건이 이번 실습 기준과 다릅니다.")

    # 조회 조건 파일에 기록된 원본을 읽습니다.
    raw_path = RAW_DIR / metadata["raw_file"]
    response = json.loads(raw_path.read_text(encoding="utf-8"))
    original = pd.DataFrame(response["output2"])

    if original.empty:
        raise ValueError("변환할 시세가 없습니다.")

    # 필요한 API 필드가 모두 존재하는지 확인합니다.
    missing = set(FIELD_MAP) - set(original.columns)
    if missing:
        raise ValueError(f"필요한 응답 필드가 없습니다: {sorted(missing)}")

    # 필요한 열을 선택하고 이름을 바꿉니다.
    # copy()로 원본 표와 별개인 작업용 표를 만듭니다.
    table = original[list(FIELD_MAP)].rename(columns=FIELD_MAP).copy()

    # 종목코드와 시장은 검증한 요청 조건을 바탕으로 추가합니다.
    table["stock_code"] = params["FID_INPUT_ISCD"]
    table["market"] = "KRX"

    for column in ["stock_code", "market"]:
        table[column] = table[column].astype("string")

    # 날짜와 숫자는 31일차에서 정한 자료형으로 변환합니다.
    # 해석할 수 없는 값은 임의 수정하지 않고 오류로 알립니다.
    table["date"] = pd.to_datetime(
        table["date"], format="%Y%m%d", errors="raise"
    ).astype("datetime64[ns]")

    for column in NUMBER_COLUMNS:
        values = table[column].replace("", pd.NA)
        table[column] = pd.to_numeric(
            values, errors="raise"
        ).astype("Int64")

    # 열 순서를 맞추고 오래된 거래일부터 정렬합니다.
    # reset_index(drop=True)는 정렬 전 행 번호를 버리고 새로 부여합니다.
    table = table[COLUMNS].sort_values("date").reset_index(drop=True)

    # 필수값 누락이나 중복이 있으면 저장 전에 멈춥니다.
    if table.isna().any().any():
        raise ValueError("필수값 누락이 있습니다. 원본 확인이 필요합니다.")

    duplicates = table.duplicated(["stock_code", "market", "date"]).sum()
    if duplicates:
        raise ValueError("동일 종목·시장·거래일 중복이 있습니다.")

    # 응답 날짜가 요청한 1월 범위 안에 있는지 검사합니다.
    in_range = table["date"].between("2025-01-01", "2025-01-31")
    if not in_range.all():
        raise ValueError("조회 기간 밖의 날짜가 있습니다.")

    # 음수와 가격 관계를 검사합니다. 이상값은 삭제하지 않습니다.
    if (table[NUMBER_COLUMNS] < 0).any().any():
        raise ValueError("가격 또는 거래량에 음수가 있습니다.")

    valid_prices = (
        (table["low"] <= table["high"])
        & table["open"].between(table["low"], table["high"])
        & table["close"].between(table["low"], table["high"])
    )
    if not valid_prices.all():
        raise ValueError("시가·종가·고가·저가 관계 확인이 필요합니다.")

    # 원본과 같은 기본 파일명을 사용해 어느 응답에서 만들었는지 연결합니다.
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CLEAN_DIR / f"{raw_path.stem}_clean.csv"
    table.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%d",
    )

    # CSV는 자료형을 기억하지 않으므로 다시 읽을 때 명시합니다.
    dtypes = {"stock_code": "string", "market": "string"}
    dtypes.update({column: "Int64" for column in NUMBER_COLUMNS})

    saved = pd.read_csv(output_path, dtype=dtypes)
    saved["date"] = pd.to_datetime(
        saved["date"], format="%Y-%m-%d", errors="raise"
    ).astype("datetime64[ns]")

    # 값·열 순서·자료형이 저장 전후 동일한지 검사합니다.
    pd.testing.assert_frame_equal(table, saved)

    print("사용한 원본:", raw_path.name)
    print("정리 결과 행·열:", saved.shape)
    print("종목코드:", saved.loc[0, "stock_code"])
    print(
        "날짜 범위:",
        saved["date"].min().strftime("%Y-%m-%d"),
        "~",
        saved["date"].max().strftime("%Y-%m-%d"),
    )
    print("기본 품질 검사: 통과")
    print("CSV 재읽기 비교: 통과")
    print("저장 위치:", output_path)


if __name__ == "__main__":
    main()