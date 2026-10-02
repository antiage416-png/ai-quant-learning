# 목적: 기존 모의 결과를 주문·체결·현금·보유수량 장부로 분리합니다.
# 입력: 40일차 신호 CSV와 41일차 일별 계좌 결과 CSV
# 처리: 주문·체결 연결 → 체결로 잔액 재계산 → 기존 결과와 대조
# 출력: 네 장부 CSV와 터미널 검증 결과
# 실제 주문·API 요청·입력 파일 변경은 없습니다.
# 초기자금·거래 규칙·비용 제외 조건은 기존 합의를 유지합니다.

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SIGNAL_PATH = (
    ROOT / "data" / "stock-day40" / "005930_2025_signals.csv"
)
ACCOUNT_PATH = (
    ROOT / "data" / "stock-day41" / "005930_2025_comparison_daily.csv"
)
OUTPUT_DIR = ROOT / "data" / "stock-day43"
INITIAL_CASH = 10_000_000

signals = pd.read_csv(SIGNAL_PATH, dtype={"stock_code": "string"})
accounts = pd.read_csv(ACCOUNT_PATH, dtype={"stock_code": "string"})

for name, frame in [("신호", signals), ("계좌", accounts)]:
    if frame.empty or not frame["stock_code"].eq("005930").all():
        raise ValueError(f"{name}: 삼성전자 자료인지 확인해야 합니다.")

    frame["date"] = pd.to_datetime(
        frame["date"], format="%Y-%m-%d", errors="raise"
    )
    if frame["date"].isna().any() or frame["date"].duplicated().any():
        raise ValueError(f"{name}: 날짜 결측 또는 중복이 있습니다.")

if set(signals["date"]) != set(accounts["date"]):
    raise ValueError("신호와 계좌의 거래일이 다릅니다.")

table = accounts.merge(
    signals[["stock_code", "date", "close_signal", "open_order"]],
    on=["stock_code", "date"],
    how="left",
    validate="one_to_one",
).sort_values("date").reset_index(drop=True)

# 금액과 수량은 정수로 확인합니다.
number_columns = [
    "open", "close", "cross_traded_shares",
    "cross_cash", "cross_shares", "cross_equity",
]
for column in number_columns:
    values = pd.to_numeric(table[column], errors="raise")
    if (
        values.isna().any()
        or values.isin([float("inf"), float("-inf")]).any()
        or values.lt(0).any()
        or values.mod(1).ne(0).any()
    ):
        raise ValueError(f"{column}: 유효한 0 이상의 정수가 아닙니다.")
    table[column] = values.astype("int64")

if table[["open", "close"]].le(0).any().any():
    raise ValueError("시가와 종가는 양수여야 합니다.")

if not table["cross_action"].isin(["없음", "매수", "매도"]).all():
    raise ValueError("정의되지 않은 거래 행동이 있습니다.")

if not table["cross_action"].eq(table["open_order"]).all():
    raise ValueError("41일차 거래와 40일차 주문 기록이 다릅니다.")

if not table["close_signal"].isin(
    ["없음", "골든크로스", "데드크로스"]
).all():
    raise ValueError("정의되지 않은 교차 신호가 있습니다.")

# 주문일에 연결된 이전 거래일의 신호를 확인합니다.
table["signal_date"] = table["date"].shift(1)
previous_signal = table["close_signal"].shift(1, fill_value="없음")

if (
    (table["cross_action"].eq("매수")
     & previous_signal.ne("골든크로스")).any()
    or
    (table["cross_action"].eq("매도")
     & previous_signal.ne("데드크로스")).any()
):
    raise ValueError("거래가 이전 거래일의 신호와 맞지 않습니다.")

# 거래 전 상태는 전날 마감 상태에서 가져옵니다.
table["cash_before"] = table["cross_cash"].shift(
    1, fill_value=INITIAL_CASH
)
table["shares_before"] = table["cross_shares"].shift(
    1, fill_value=0
)

no_trade = table["cross_action"].eq("없음")
if table.loc[no_trade, "cross_traded_shares"].ne(0).any():
    raise ValueError("거래가 없는 날에 거래 수량이 기록돼 있습니다.")

order_records = []
fill_records = []

trade_rows = table.loc[~no_trade]

for number, row in enumerate(trade_rows.itertuples(index=False), start=1):
    quantity = int(row.cross_traded_shares)
    price = int(row.open)

    if quantity <= 0:
        raise ValueError("거래일의 체결 수량은 양수여야 합니다.")

    if pd.isna(row.signal_date) or row.signal_date >= row.date:
        raise ValueError("신호확인일과 주문일의 순서가 잘못됐습니다.")

    if row.cross_action == "매수":
        if row.shares_before != 0 or quantity != row.cash_before // price:
            raise ValueError("최대 정수 수량 매수 규칙과 다릅니다.")
        policy = "가용 현금 내 최대 정수 수량"
    else:
        if row.shares_before <= 0 or quantity != row.shares_before:
            raise ValueError("보유 전량 매도 규칙과 다릅니다.")
        policy = "보유 전량"

    # 번호는 기록을 연결하기 위한 ID이며 거래 조건을 바꾸지 않습니다.
    order_id = f"O{number:03d}"
    fill_id = f"F{number:03d}"

    order_records.append({
        "order_id": order_id,
        "stock_code": "005930",
        "signal_date": row.signal_date,
        "order_date": row.date,
        "action": row.cross_action,
        "quantity_policy": policy,
        "status": "모의체결완료",
    })
    fill_records.append({
        "fill_id": fill_id,
        "order_id": order_id,
        "stock_code": "005930",
        "fill_date": row.date,
        "action": row.cross_action,
        "quantity": quantity,
        "price": price,
        "amount": quantity * price,
    })

orders = pd.DataFrame(order_records, columns=[
    "order_id", "stock_code", "signal_date", "order_date",
    "action", "quantity_policy", "status",
])
fills = pd.DataFrame(fill_records, columns=[
    "fill_id", "order_id", "stock_code", "fill_date",
    "action", "quantity", "price", "amount",
])

# 이번 사례는 주문마다 한 번씩 전량 모의 체결된 결과입니다.
# 주문·체결의 ID와 행동·날짜 연결을 검사합니다.
if orders["order_id"].duplicated().any() or fills["fill_id"].duplicated().any():
    raise ValueError("중복 ID가 있습니다.")

if set(orders["order_id"]) != set(fills["order_id"]):
    raise ValueError("주문과 체결의 연결이 다릅니다.")

linked = fills.merge(
    orders,
    on=["order_id", "stock_code"],
    validate="one_to_one",
    suffixes=("_fill", "_order"),
)
if (
    not linked["action_fill"].eq(linked["action_order"]).all()
    or not linked["fill_date"].eq(linked["order_date"]).all()
):
    raise ValueError("주문과 체결의 행동 또는 날짜가 다릅니다.")

# 매수는 현금 감소·수량 증가, 매도는 현금 증가·수량 감소입니다.
impact = fills.copy()
impact["cash_change"] = impact["amount"].where(
    impact["action"].eq("매도"), -impact["amount"]
)
impact["shares_change"] = impact["quantity"].where(
    impact["action"].eq("매수"), -impact["quantity"]
)

# 거래 없는 날에도 변화량 0을 기록해 모든 날짜를 유지합니다.
changes = impact.groupby("fill_date")[[
    "cash_change", "shares_change"
]].sum().reindex(
    pd.DatetimeIndex(table["date"]), fill_value=0
).astype("int64")
changes.index = table.index

# cumsum은 체결에 따른 변화를 앞에서부터 누적해서 더합니다.
cash_after = INITIAL_CASH + changes["cash_change"].cumsum()
shares_after = changes["shares_change"].cumsum()
stock_value = shares_after * table["close"]
equity = cash_after + stock_value

if cash_after.lt(0).any() or shares_after.lt(0).any():
    raise ValueError("재계산한 현금 또는 보유수량이 음수입니다.")

# 마지막 값뿐 아니라 모든 거래일의 기존 계좌 결과와 비교합니다.
for actual, expected, name in [
    (cash_after, table["cross_cash"], "현금"),
    (shares_after, table["cross_shares"], "보유수량"),
    (equity, table["cross_equity"], "자산가치"),
]:
    if actual.tolist() != expected.tolist():
        raise ValueError(f"체결에서 재계산한 {name}이 41일차와 다릅니다.")

# 날짜별 체결ID를 남겨 장부 변화의 근거를 찾을 수 있게 합니다.
fill_ids = table["date"].map(
    fills.set_index("fill_date")["fill_id"]
).fillna("")

cash_book = pd.DataFrame({
    "date": table["date"],
    "stock_code": "005930",
    "fill_id": fill_ids,
    "cash_before": cash_after.shift(1, fill_value=INITIAL_CASH),
    "cash_change": changes["cash_change"],
    "cash_after": cash_after,
})
position_book = pd.DataFrame({
    "date": table["date"],
    "stock_code": "005930",
    "fill_id": fill_ids,
    "shares_before": shares_after.shift(1, fill_value=0),
    "shares_change": changes["shares_change"],
    "shares_after": shares_after,
    "close": table["close"],
    "stock_value": stock_value,
})

# 네 기록을 각각 별도 CSV로 저장합니다.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
for filename, book in [
    ("orders.csv", orders),
    ("fills.csv", fills),
    ("cash_ledger.csv", cash_book),
    ("positions.csv", position_book),
]:
    book.to_csv(OUTPUT_DIR / filename, index=False)

print(f"공통 초기자금: {INITIAL_CASH:,.0f}원")
print(f"주문 기록: {len(orders)}건")
print(f"모의 체결 기록: {len(fills)}건")
print(f"현금 장부: {len(cash_book)}행")
print(f"보유수량 장부: {len(position_book)}행")
print("주문·체결 연결 검사: 통과")
print("최대 정수 수량·전량 매도 규칙 검사: 통과")
print("41일차 전체 거래일 현금·수량·자산가치 대조: 통과")
print(f"\n최종 현금: {cash_after.iloc[-1]:,.0f}원")
print(f"최종 보유수량: {shares_after.iloc[-1]}주")
print(f"최종 주식 평가액: {stock_value.iloc[-1]:,.0f}원")
print(f"최종 자산가치: {equity.iloc[-1]:,.0f}원")
print(f"\n네 장부 저장 위치: {OUTPUT_DIR}")
print("실제 API 요청·주문: 없음")