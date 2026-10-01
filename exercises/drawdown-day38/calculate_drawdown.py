# 목적: 삼성전자 가격으로 자산가치·낙폭을 계산하고 그래프로 확인합니다.
# 입력: 검증한 삼성전자 종가 CSV
# 처리: 종가 × 10 → 누적 최고값 → 낙폭 → 최대낙폭
# 출력: 결과 CSV, 그래프 PNG, 터미널 요약
# API 요청은 없으며 입력 CSV는 변경하지 않습니다.

from math import isclose
from pathlib import Path

import matplotlib

# 화면 창 없이 이미지 파일을 저장하는 방식을 사용합니다.
# WSL에서 별도의 그래픽 창 설정 없이 실행할 수 있습니다.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data" / "stock-day33" / "clean" / "005930_2025_clean.csv"
OUTPUT_DIR = ROOT / "data" / "stock-day38"
CSV_PATH = OUTPUT_DIR / "005930_2025_drawdown.csv"
PNG_PATH = OUTPUT_DIR / "005930_2025_drawdown.png"

# 실제 주문 수량이 아니라 자산가치 계산을 위한 고정 배수입니다.
UNITS = 1

table = pd.read_csv(INPUT_PATH, dtype=str, keep_default_na=False)
result = table[["stock_code", "market", "date", "close"]].copy()

if len(result) < 2:
    raise ValueError("최소 두 행의 가격이 필요합니다.")

if not result["stock_code"].eq("005930").all():
    raise ValueError("삼성전자가 아닌 종목코드가 있습니다.")

if not result["market"].eq("KRX").all():
    raise ValueError("시장 정보가 KRX인지 확인해야 합니다.")

# 날짜와 가격을 변환하고 계산에 사용할 수 없는 값을 검사합니다.
result["date"] = pd.to_datetime(
    result["date"], format="%Y-%m-%d", errors="raise"
)
result["close"] = pd.to_numeric(result["close"], errors="raise")

if result["date"].isna().any() or result["date"].duplicated().any():
    raise ValueError("날짜 결측값 또는 중복 날짜가 있습니다.")

if (
    result["close"].isna().any()
    or result["close"].le(0).any()
    or result["close"].isin([float("inf"), float("-inf")]).any()
):
    raise ValueError("종가에 결측값, 0 이하 또는 무한대가 있습니다.")

result = result.sort_values("date").reset_index(drop=True)

# 모형의 자산가치와 처음 대비 누적수익률을 계산합니다.
result["equity"] = result["close"] * UNITS
result["cumulative_return"] = (
    result["equity"] / result["equity"].iloc[0] - 1
)

# 각 시점까지의 최고값만 사용합니다. 미래 가격은 사용하지 않습니다.
result["running_peak"] = result["equity"].cummax()
result["drawdown"] = result["equity"] / result["running_peak"] - 1

# idxmin은 최솟값이 있는 행 번호를 반환합니다.
# 최솟값이 여러 번 나오면 첫 번째 발생 시점을 선택합니다.
trough_index = result["drawdown"].idxmin()
max_drawdown = result.loc[trough_index, "drawdown"]
trough_date = result.loc[trough_index, "date"]

# 최대낙폭 저점 이전에 형성된 기준 고점을 찾습니다.
# 동일한 고점이 여러 번 있으면 저점 직전의 마지막 고점을 선택합니다.
before_trough = result.loc[:trough_index]
peak_value = result.loc[trough_index, "running_peak"]
peak_index = before_trough[
    before_trough["equity"].eq(peak_value)
].index[-1]
peak_date = result.loc[peak_index, "date"]

# 계산된 낙폭은 양수가 될 수 없고, 최고값은 감소하면 안 됩니다.
if result["drawdown"].gt(0).any():
    raise ValueError("양수인 낙폭이 있습니다.")

if not result["running_peak"].is_monotonic_increasing:
    raise ValueError("누적 최고값이 감소하는 구간이 있습니다.")

# 고정 배수를 곱해도 누적수익률은 원래 가격 수익률과 같아야 합니다.
price_return = result["close"] / result["close"].iloc[0] - 1
for actual, expected in zip(result["cumulative_return"], price_return):
    if not isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError("가격 수익률과 자산가치 수익률이 다릅니다.")

# 보고한 고점·저점으로 최대낙폭을 다시 계산해 확인합니다.
checked_mdd = result.loc[trough_index, "equity"] / peak_value - 1
if not isclose(max_drawdown, checked_mdd, rel_tol=1e-9, abs_tol=1e-12):
    raise ValueError("고점·저점으로 계산한 최대낙폭과 다릅니다.")

# 원본과 별도의 폴더에 결과를 저장합니다.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
result.to_csv(CSV_PATH, index=False)

# 저장 전후 날짜와 숫자가 보존됐는지 확인합니다.
loaded = pd.read_csv(
    CSV_PATH,
    dtype={"stock_code": "string", "market": "string"},
    parse_dates=["date"],
)
check_columns = [
    "date", "close", "equity",
    "cumulative_return", "running_peak", "drawdown",
]
pd.testing.assert_frame_equal(
    result[check_columns],
    loaded[check_columns],
    check_exact=False,
    rtol=1e-9,
    atol=1e-12,
)

# 두 그래프가 날짜 축을 공유하도록 만듭니다.
fig, axes = plt.subplots(
    2, 1, figsize=(11, 7), sharex=True, layout="constrained"
)
equity_ax, drawdown_ax = axes

# 위쪽: 현재 자산가치와 그때까지의 최고 자산가치를 비교합니다.
equity_ax.plot(result["date"], result["equity"], label="Equity")
equity_ax.plot(
    result["date"],
    result["running_peak"],
    linestyle="--",
    label="Running peak",
)
equity_ax.set_title("005930 | 1-share value (close price) | 2025")
equity_ax.set_ylabel("Value (KRW)")
equity_ax.ticklabel_format(axis="y", style="plain")
equity_ax.legend()
equity_ax.grid(alpha=0.3)

# 아래쪽: 낙폭을 퍼센트 단위로 표시하고 음수 구간을 채웁니다.
drawdown_percent = result["drawdown"] * 100
drawdown_ax.plot(result["date"], drawdown_percent, color="tab:red")
drawdown_ax.fill_between(
    result["date"], drawdown_percent, 0,
    color="tab:red", alpha=0.2,
)
drawdown_ax.axhline(0, color="gray", linewidth=0.8)
drawdown_ax.set_title(f"Maximum drawdown: {max_drawdown:.2%}")
drawdown_ax.set_ylabel("Drawdown (%)")
drawdown_ax.set_xlabel("Date")
drawdown_ax.grid(alpha=0.3)

# 실제 하락이 있을 때만 최대낙폭의 고점과 저점을 표시합니다.
if max_drawdown < 0:
    equity_ax.scatter(
        [peak_date, trough_date],
        [peak_value, result.loc[trough_index, "equity"]],
        color="tab:red",
        zorder=3,
    )
    drawdown_ax.scatter(
        [trough_date], [max_drawdown * 100],
        color="black", zorder=3,
    )

# dpi는 저장 이미지의 해상도 설정입니다.
fig.savefig(PNG_PATH, dpi=150)
plt.close(fig)

print(f"matplotlib 버전: {matplotlib.__version__}")
print(f"전체 행 수: {len(result)}")
print(f"시작 자산가치: {result['equity'].iloc[0]:,.0f}원")
print(f"마지막 자산가치: {result['equity'].iloc[-1]:,.0f}원")
print(f"최종 누적수익률: {result['cumulative_return'].iloc[-1]:.4%}")
print(f"최대낙폭(MDD): {max_drawdown:.4%}")

if max_drawdown < 0:
    print(f"최대낙폭 기준 고점 날짜: {peak_date:%Y-%m-%d}")
    print(f"최대낙폭 저점 날짜: {trough_date:%Y-%m-%d}")
else:
    print("관측 기간에 고점 대비 하락이 없습니다.")

print("계산 검증: 통과")
print("CSV 재읽기 비교: 통과")
print(f"CSV 저장: {CSV_PATH}")
print(f"그래프 저장: {PNG_PATH}")