# 목적: 교차 전략과 매수 후 보유 전략을 같은 기간·자금으로 비교합니다.
# 입력: 삼성전자 가격 CSV와 40일차의 모의 주문 기록
# 처리: 시가 매매 → 종가 평가 → 수익률·최대낙폭 비교
# 출력: 일별 계산 CSV, 비교 요약 CSV, 터미널 결과
# 실제 주문·API 요청·입력 파일 변경은 없습니다.
# 비용·배당·현금 이자는 제외하며 결과는 비용 차감 전입니다.

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PRICE_PATH = (
    ROOT / "data" / "stock-day33" / "clean" / "005930_2025_clean.csv"
)
SIGNAL_PATH = (
    ROOT / "data" / "stock-day40" / "005930_2025_signals.csv"
)
OUTPUT_DIR = ROOT / "data" / "stock-day41"
DAILY_PATH = OUTPUT_DIR / "005930_2025_comparison_daily.csv"
SUMMARY_PATH = OUTPUT_DIR / "005930_2025_comparison_summary.csv"

# 사용자와 합의한 공통 초기자금입니다.
INITIAL_CASH = 10_000_000

prices = pd.read_csv(PRICE_PATH, dtype=str, keep_default_na=False)
signals = pd.read_csv(SIGNAL_PATH, dtype=str, keep_default_na=False)

# 두 입력의 종목·날짜를 확인합니다.
for name, frame in [("가격", prices), ("신호", signals)]:
    if frame.empty or not frame["stock_code"].eq("005930").all():
        raise ValueError(f"{name}: 삼성전자 자료인지 확인해야 합니다.")

    frame["date"] = pd.to_datetime(
        frame["date"], format="%Y-%m-%d", errors="raise"
    )
    if frame["date"].isna().any() or frame["date"].duplicated().any():
        raise ValueError(f"{name}: 날짜 결측 또는 중복이 있습니다.")

if not prices["market"].eq("KRX").all():
    raise ValueError("가격 자료의 시장이 KRX인지 확인해야 합니다.")

if set(prices["date"]) != set(signals["date"]):
    raise ValueError("가격과 신호의 날짜 집합이 다릅니다.")

# 가격은 원 단위 정수로 계산해 현금·수량 계산을 명확하게 합니다.
for column in ["open", "close"]:
    values = pd.to_numeric(prices[column], errors="raise")
    if (
        values.isna().any()
        or values.le(0).any()
        or values.isin([float("inf"), float("-inf")]).any()
        or values.mod(1).ne(0).any()
    ):
        raise ValueError(f"{column}: 유효한 양의 정수 가격이 아닙니다.")
    prices[column] = values.astype("int64")

# 같은 종목·날짜끼리 연결하고 시간순으로 정렬합니다.
table = prices[["stock_code", "date", "open", "close"]].merge(
    signals[["stock_code", "date", "close_signal", "open_order"]],
    on=["stock_code", "date"],
    how="left",
    validate="one_to_one",
).sort_values("date").reset_index(drop=True)

if not table["open_order"].isin(["없음", "매수", "매도"]).all():
    raise ValueError("정의되지 않은 주문 행동이 있습니다.")

if not table["close_signal"].isin(
    ["없음", "골든크로스", "데드크로스"]
).all():
    raise ValueError("정의되지 않은 교차 신호가 있습니다.")

# 40일차 open_order는 이미 다음 거래일에 배치된 기록입니다.
# 주문을 다시 shift하지 않고 전날 신호와 연결됐는지만 확인합니다.
previous_signal = table["close_signal"].shift(1, fill_value="없음")
if (
    (table["open_order"].eq("매수")
     & previous_signal.ne("골든크로스")).any()
    or
    (table["open_order"].eq("매도")
     & previous_signal.ne("데드크로스")).any()
):
    raise ValueError("주문이 이전 거래일의 교차 신호와 맞지 않습니다.")


def simulate(orders):
    # 두 전략 모두 같은 현금과 미보유 상태에서 시작합니다.
    cash = INITIAL_CASH
    shares = 0

    # 첫날 종가가 초기자금보다 낮아도 낙폭에 포함하도록 합니다.
    peak = INITIAL_CASH
    records = []

    if len(orders) != len(table):
        raise ValueError("주문 수와 가격 행 수가 다릅니다.")

    for row, action in zip(table.itertuples(index=False), orders):
        traded = 0

        if action == "매수":
            if shares != 0:
                raise ValueError("보유 중 추가 매수는 허용하지 않습니다.")

            traded = cash // row.open
            if traded == 0:
                raise ValueError(
                    f"{row.date:%Y-%m-%d}: 1주를 매수할 현금이 부족합니다."
                )
            cash -= traded * row.open
            shares = traded

        elif action == "매도":
            if shares == 0:
                raise ValueError("미보유 상태에서는 매도할 수 없습니다.")

            traded = shares
            cash += shares * row.open
            shares = 0

        elif action != "없음":
            raise ValueError("정의되지 않은 행동입니다.")

        if cash < 0 or shares < 0:
            raise ValueError("현금이나 보유 수량이 음수가 됐습니다.")

        # 시가 거래 후 남은 현금과 주식을 당일 종가로 평가합니다.
        equity = cash + shares * row.close
        peak = max(peak, equity)

        records.append({
            "action": action,
            "traded_shares": traded,
            "cash": cash,
            "shares": shares,
            "equity": equity,
            "cumulative_return": equity / INITIAL_CASH - 1,
            "running_peak": peak,
            "drawdown": equity / peak - 1,
        })

    return pd.DataFrame(records)


# 교차 전략은 40일차의 주문일을 그대로 사용합니다.
cross_account = simulate(table["open_order"].tolist())

# 기준전략은 첫 거래일 시가에 한 번 매수하고 끝까지 유지합니다.
hold_orders = ["매수"] + ["없음"] * (len(table) - 1)
hold_account = simulate(hold_orders)

# 두 전략의 일별 결과를 같은 날짜 옆에 나란히 기록합니다.
daily = table[["stock_code", "date", "open", "close"]].copy()
summary_rows = []

for prefix, name, account in [
    ("cross", "교차 전략", cross_account),
    ("hold", "매수 후 보유", hold_account),
]:
    for column in account.columns:
        daily[f"{prefix}_{column}"] = account[column]

    final = account.iloc[-1]
    summary_rows.append({
        "전략": name,
        "초기자금": INITIAL_CASH,
        "최종현금": int(final["cash"]),
        "최종보유수량": int(final["shares"]),
        "최종자산": int(final["equity"]),
        "최종손익": int(final["equity"]) - INITIAL_CASH,
        "수익률": final["cumulative_return"],
        "최대낙폭": account["drawdown"].min(),
        "매수횟수": int(account["action"].eq("매수").sum()),
        "매도횟수": int(account["action"].eq("매도").sum()),
    })

summary = pd.DataFrame(summary_rows)

# 마지막 날 강제 매도 없이 종가 평가액을 저장합니다.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
daily.to_csv(DAILY_PATH, index=False)
summary.to_csv(SUMMARY_PATH, index=False)

# 일별 결과를 다시 읽어 금액·수량·비율이 보존됐는지 비교합니다.
loaded = pd.read_csv(
    DAILY_PATH,
    dtype={"stock_code": "string"},
    parse_dates=["date"],
)
pd.testing.assert_frame_equal(
    daily,
    loaded,
    check_dtype=False,
    check_exact=False,
    rtol=1e-9,
    atol=1e-12,
)

# 화면에서만 수익률과 낙폭을 퍼센트로 표시합니다.
display = summary.copy()
display["수익률"] *= 100
display["최대낙폭"] *= 100
display = display.rename(columns={
    "수익률": "수익률(%)",
    "최대낙폭": "최대낙폭(%)",
})

print(f"공통 초기자금: {INITIAL_CASH:,.0f}원")
print(
    f"공통 기간: {table['date'].iloc[0]:%Y-%m-%d}"
    f" ~ {table['date'].iloc[-1]:%Y-%m-%d}"
)
print(f"전체 행 수: {len(table)}")
print(f"첫 거래일 시가: {table['open'].iloc[0]:,}원")
print(f"기준전략 매수 수량: {hold_account['shares'].iloc[0]}주")
print(f"기준전략 매수 후 현금: {hold_account['cash'].iloc[0]:,}원")
print("\n비용 차감 전 비교:")
print(display.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
print("\n입력 연결·주문 시점 검사: 통과")
print("일별 CSV 재읽기 비교: 통과")
print("실제 API 요청·주문: 없음")
print(f"일별 결과 저장: {DAILY_PATH}")
print(f"비교 요약 저장: {SUMMARY_PATH}")

