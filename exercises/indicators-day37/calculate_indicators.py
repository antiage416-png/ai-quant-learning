# 목적: 이동평균·수익률 변동성·거래량 평균과 초기 결측 구간을 확인합니다.
# 입력: 검증한 삼성전자 종가·거래량 CSV
# 처리: 날짜 정렬 → 입력 검사 → 지표 계산 → 결측 구간 검사
# 출력: 지표 CSV와 터미널 요약
# API 요청은 없으며, 입력 CSV는 변경하지 않습니다.

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data" / "stock-day33" / "clean" / "005930_2025_clean.csv"
OUTPUT_DIR = ROOT / "data" / "stock-day37"
OUTPUT_PATH = OUTPUT_DIR / "005930_2025_indicators.csv"

# 문자열로 읽어 종목코드의 앞자리 0을 보존합니다.
table = pd.read_csv(INPUT_PATH, dtype=str, keep_default_na=False)
result = table[["stock_code", "market", "date", "close", "volume"]].copy()

if len(result) < 21:
    raise ValueError("이번 지표를 모두 계산하려면 최소 21행이 필요합니다.")

if not result["stock_code"].eq("005930").all():
    raise ValueError("삼성전자가 아닌 종목코드가 있습니다.")

if not result["market"].eq("KRX").all():
    raise ValueError("시장 정보가 KRX인지 확인해야 합니다.")

# 변환할 수 없는 값은 임의로 채우지 않고 오류로 처리합니다.
result["date"] = pd.to_datetime(
    result["date"], format="%Y-%m-%d", errors="raise"
)

for column in ["close", "volume"]:
    result[column] = pd.to_numeric(result[column], errors="raise")

    if (
        result[column].isna().any()
        or result[column].isin([float("inf"), float("-inf")]).any()
    ):
        raise ValueError(f"{column}: 결측값 또는 무한대가 있습니다.")

if result["date"].isna().any() or result["date"].duplicated().any():
    raise ValueError("날짜 결측값 또는 중복 날짜가 있습니다.")

if result["close"].le(0).any():
    raise ValueError("종가는 양수여야 합니다.")

if result["volume"].lt(0).any():
    raise ValueError("거래량에 음수가 있습니다.")

# 날짜순으로 정렬해 각 행이 시간 순서를 따르게 합니다.
result = result.sort_values("date").reset_index(drop=True)

# 첫 행의 일간수익률은 이전 가격이 없으므로 NaN입니다.
result["daily_return"] = result["close"].pct_change(fill_method=None)

# 현재 행을 포함한 최근 5개·20개 종가의 평균입니다.
result["ma_5"] = result["close"].rolling(
    window=5, min_periods=5
).mean()
result["ma_20"] = result["close"].rolling(
    window=20, min_periods=20
).mean()

# 최근 유효한 일간수익률 20개로 표본 표준편차를 계산합니다.
# ddof=1은 분산 계산에서 분모를 표본 수보다 1 작게 사용합니다.
# 결과는 일간수익률과 같은 소수 단위이며, 연율화하지 않습니다.
result["volatility_20"] = result["daily_return"].rolling(
    window=20, min_periods=20
).std(ddof=1)

# 현재 거래일을 포함한 최근 20개 거래량의 평균입니다.
result["volume_ma_20"] = result["volume"].rolling(
    window=20, min_periods=20
).mean()

# 입력에 결측값이 없을 때 예상되는 초기 결측 행 수입니다.
expected_missing = {
    "daily_return": 1,
    "ma_5": 4,
    "ma_20": 19,
    "volatility_20": 20,
    "volume_ma_20": 19,
}

print("지표별 초기 결측 구간:")

for column, missing_count in expected_missing.items():
    values = result[column]

    # 처음 구간은 비어 있어야 하고, 그 뒤에는 값이 있어야 합니다.
    initial_is_missing = values.iloc[:missing_count].isna().all()
    remaining_is_valid = values.iloc[missing_count:].notna().all()

    if not initial_is_missing or not remaining_is_valid:
        raise ValueError(f"{column}: 예상한 결측 구간과 다릅니다.")

    if values.isin([float("inf"), float("-inf")]).any():
        raise ValueError(f"{column}: 무한대가 있습니다.")

    first_date = result.loc[missing_count, "date"]
    print(
        f"{column}: 결측 {values.isna().sum()}개"
        f" / 첫 유효 날짜 {first_date:%Y-%m-%d}"
    )

# 검사한 결측값은 그대로 보존합니다.
# 0이나 미래 값으로 채우지 않고, 별도의 결과 CSV를 저장합니다.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
result.to_csv(OUTPUT_PATH, index=False, na_rep="")

# 저장 전후 숫자와 결측 위치가 보존됐는지 비교합니다.
loaded = pd.read_csv(
    OUTPUT_PATH,
    dtype={"stock_code": "string", "market": "string"},
    parse_dates=["date"],
)
check_columns = ["date", "close", "volume", *expected_missing]

pd.testing.assert_frame_equal(
    result[check_columns],
    loaded[check_columns],
    check_exact=False,
    rtol=1e-9,
    atol=1e-12,
)

# 화면에서만 수익률과 변동성을 100배 해 퍼센트 단위로 표시합니다.
preview = result[
    ["date", "close", "ma_5", "ma_20", "volume", "volume_ma_20"]
].copy()
preview["일간수익률(%)"] = result["daily_return"] * 100
preview["변동성_20(%)"] = result["volatility_20"] * 100

print("\n마지막 3행:")
print(
    preview.tail(3).to_string(
        index=False,
        float_format=lambda value: f"{value:.4f}",
    )
)

print(f"\n전체 행 수: {len(result)}")
print("초기 결측 구간 검사: 통과")
print("CSV 재읽기 비교: 통과")
print(f"저장 위치: {OUTPUT_PATH}")