# 목적: 삼성전자 종가의 일간수익률과 누적수익률을 계산합니다.
# 입력: 33일차에서 저장하고 검증한 삼성전자 CSV
# 처리: 날짜 정렬 → 종가 검사 → 수익률 계산 → 두 계산법 비교
# 출력: 터미널 요약과 수익률 CSV
# API 요청은 없으며, 입력 CSV는 변경하지 않습니다.

from math import isclose
from pathlib import Path

import pandas as pd


# 현재 코드 위치를 기준으로 입력과 출력 경로를 정합니다.
ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data" / "stock-day33" / "clean" / "005930_2025_clean.csv"
OUTPUT_DIR = ROOT / "data" / "stock-day36"
OUTPUT_PATH = OUTPUT_DIR / "005930_2025_returns.csv"

# 종목코드의 앞자리 0을 보존하도록 문자열로 읽습니다.
table = pd.read_csv(INPUT_PATH, dtype=str, keep_default_na=False)

# 수익률 계산에 필요한 열만 복사합니다.
# copy는 원래 표와 분리해서 작업하겠다는 뜻입니다.
result = table[["stock_code", "market", "date", "close"]].copy()

if len(result) < 2:
    raise ValueError("수익률 비교에는 최소 두 행이 필요합니다.")

if not result["stock_code"].eq("005930").all():
    raise ValueError("삼성전자가 아닌 종목코드가 있습니다.")

if not result["market"].eq("KRX").all():
    raise ValueError("시장 정보가 KRX인지 확인해야 합니다.")

# 날짜와 종가를 계산 가능한 자료형으로 변환합니다.
# errors='raise'는 변환할 수 없는 값이 있으면 중단하는 설정입니다.
result["date"] = pd.to_datetime(
    result["date"], format="%Y-%m-%d", errors="raise"
)
result["close"] = pd.to_numeric(result["close"], errors="raise")

if result["date"].isna().any() or result["date"].duplicated().any():
    raise ValueError("날짜 결측값 또는 중복 날짜가 있습니다.")

# 분모가 되는 종가는 양수여야 합니다.
# 무한대도 정상적인 가격으로 사용하지 않습니다.
if (
    result["close"].isna().any()
    or result["close"].le(0).any()
    or result["close"].isin([float("inf"), float("-inf")]).any()
):
    raise ValueError("종가에 결측값, 0 이하 또는 무한대가 있습니다.")

# 날짜순으로 정렬해야 직전 행이 직전 거래일을 뜻합니다.
# reset_index(drop=True)는 기존 행 번호 대신 0부터 새 번호를 붙입니다.
result = result.sort_values("date").reset_index(drop=True)
close = result["close"]

# 수익률은 소수 단위로 저장합니다. 0.01은 1%입니다.
result["daily_return"] = close.pct_change(fill_method=None)
result["cumulative_return"] = close / close.iloc[0] - 1

# 일간수익률의 누적 곱으로도 같은 결과가 나오는지 확인합니다.
factor = 1 + result["daily_return"]
factor.iloc[0] = 1.0
compound_return = factor.cumprod() - 1

for direct, compound in zip(result["cumulative_return"], compound_return):
    if not isclose(direct, compound, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError("누적수익률 두 계산법이 일치하지 않습니다.")

# 입력 가격에 결측값이 없으므로 일간수익률은 첫 행만 비어야 합니다.
if not pd.isna(result.loc[0, "daily_return"]):
    raise ValueError("첫날 일간수익률이 결측값인지 확인해야 합니다.")

if result["daily_return"].iloc[1:].isna().any():
    raise ValueError("첫날 이외의 일간수익률에 결측값이 있습니다.")

# 출력 폴더를 만들고 별도의 CSV로 저장합니다.
# 첫날 일간수익률의 NaN은 CSV에서 빈칸으로 기록합니다.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
result.to_csv(OUTPUT_PATH, index=False, na_rep="")

# 저장한 파일을 다시 읽고 행 수와 수익률 값이 보존됐는지 확인합니다.
loaded = pd.read_csv(
    OUTPUT_PATH,
    dtype={"stock_code": "string", "market": "string"},
    parse_dates=["date"],
)
pd.testing.assert_frame_equal(
    result[["date", "daily_return", "cumulative_return"]],
    loaded[["date", "daily_return", "cumulative_return"]],
    check_exact=False,
    rtol=1e-9,
    atol=1e-12,
)

# 화면에서만 퍼센트로 변환합니다. 저장된 값은 소수 단위를 유지합니다.
preview = result[["date", "close"]].copy()
preview["일간수익률(%)"] = result["daily_return"] * 100
preview["누적수익률(%)"] = result["cumulative_return"] * 100

print("처음 3행:")
print(preview.head(3).to_string(index=False, float_format=lambda x: f"{x:.4f}"))
print("\n마지막 3행:")
print(preview.tail(3).to_string(index=False, float_format=lambda x: f"{x:.4f}"))

print(f"\n전체 행 수: {len(result)}")
print(f"계산 가능한 일간수익률 수: {result['daily_return'].count()}")
print(f"기준일: {result['date'].iloc[0]:%Y-%m-%d}")
print(f"마지막 날짜: {result['date'].iloc[-1]:%Y-%m-%d}")
print(f"기준일 종가: {close.iloc[0]:,.0f}")
print(f"마지막 종가: {close.iloc[-1]:,.0f}")
print(f"기준일 종가 대비 누적수익률: {result['cumulative_return'].iloc[-1]:.4%}")
print("누적수익률 두 계산법 비교: 통과")
print("CSV 재읽기 비교: 통과")
print(f"저장 위치: {OUTPUT_PATH}")