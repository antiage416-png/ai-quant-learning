# 목적: 두 전략의 자산가치와 낙폭을 같은 날짜 축으로 비교합니다.
# 입력: 41일차에 저장한 일별 비교 CSV
# 처리: 자산가치는 원 단위, 낙폭은 퍼센트 단위로 시각화합니다.
# 출력: 비교 그래프 PNG
# 계산 CSV 변경·API 요청·실제 주문은 없습니다.

from pathlib import Path

import matplotlib

# WSL에서 그래픽 창 없이 PNG를 저장합니다.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = (
    ROOT / "data" / "stock-day41" / "005930_2025_comparison_daily.csv"
)
PNG_PATH = INPUT_PATH.with_name("005930_2025_comparison.png")
INITIAL_CASH = 10_000_000

table = pd.read_csv(INPUT_PATH, parse_dates=["date"])
table = table.sort_values("date").reset_index(drop=True)

if table.empty or table["date"].isna().any():
    raise ValueError("일별 결과가 비어 있거나 날짜가 없습니다.")

if table["date"].duplicated().any():
    raise ValueError("중복 날짜가 있습니다.")

# 그래프에 필요한 값이 유효한지 확인합니다.
columns = [
    "cross_equity", "hold_equity",
    "cross_drawdown", "hold_drawdown",
]
for column in columns:
    table[column] = pd.to_numeric(table[column], errors="raise")
    if (
        table[column].isna().any()
        or table[column].isin([float("inf"), float("-inf")]).any()
    ):
        raise ValueError(f"{column}에 결측값 또는 무한대가 있습니다.")

# 위쪽은 자산가치, 아래쪽은 낙폭이며 날짜 축을 공유합니다.
fig, axes = plt.subplots(
    2, 1, figsize=(12, 8), sharex=True, layout="constrained"
)
equity_ax, drawdown_ax = axes

for prefix, label, color in [
    ("cross", "MA cross", "tab:blue"),
    ("hold", "Buy and hold", "tab:orange"),
]:
    equity_ax.plot(
        table["date"], table[f"{prefix}_equity"],
        label=label, color=color,
    )

    # CSV의 소수 단위 낙폭을 화면에서만 퍼센트로 바꿉니다.
    mdd = table[f"{prefix}_drawdown"].min()
    drawdown_ax.plot(
        table["date"], table[f"{prefix}_drawdown"] * 100,
        label=f"{label} | MDD {mdd:.2%}", color=color,
    )

# 합의한 초기자금을 기준선으로 표시합니다.
# 첫날 마감 자산을 억지로 초기자금과 같게 맞추지 않습니다.
equity_ax.axhline(
    INITIAL_CASH, color="gray", linestyle=":",
    label="Initial cash: 10,000,000 KRW",
)
equity_ax.set_title("005930 | Same initial cash | Before costs | 2025")
equity_ax.set_ylabel("Equity (KRW)")
equity_ax.ticklabel_format(axis="y", style="plain", useOffset=False)
equity_ax.legend()
equity_ax.grid(alpha=0.3)

drawdown_ax.axhline(0, color="gray", linewidth=0.8)
drawdown_ax.set_ylabel("Drawdown (%)")
drawdown_ax.set_xlabel("Date")
drawdown_ax.legend()
drawdown_ax.grid(alpha=0.3)

fig.savefig(PNG_PATH, dpi=150)
plt.close(fig)

print(f"비교한 행 수: {len(table)}")
print("위쪽: 초기자금 1,000만원 기준 자산가치, 원 단위")
print("아래쪽: 초기자금을 포함한 누적 최고값 대비 낙폭")
print(f"그래프 저장: {PNG_PATH}")