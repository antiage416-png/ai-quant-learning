# 목적: 삼성전자 교차 신호와 다음 거래일 모의 주문을 구분합니다.
# 입력: 37일차 이동평균 CSV와 33일차 가격 CSV
# 처리: 날짜 연결 → 교차 판단 → 전날 신호로 오늘 모의 주문 결정
# 출력: 전체 신호 CSV, 모의 주문 목록 CSV, 터미널 요약
# 실제 주문·API 요청·입력 파일 변경은 없습니다.

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INDICATOR_PATH = (
    ROOT / "data" / "stock-day37" / "005930_2025_indicators.csv"
)
PRICE_PATH = (
    ROOT / "data" / "stock-day33" / "clean" / "005930_2025_clean.csv"
)
OUTPUT_DIR = ROOT / "data" / "stock-day40"
SIGNAL_PATH = OUTPUT_DIR / "005930_2025_signals.csv"
ORDER_PATH = OUTPUT_DIR / "005930_2025_orders.csv"

indicators = pd.read_csv(
    INDICATOR_PATH, dtype={"stock_code": "string"}
)
prices = pd.read_csv(
    PRICE_PATH, dtype={"stock_code": "string"}
)

# 두 파일 모두 같은 종목·시장의 날짜별 자료인지 확인합니다.
for name, frame in [("지표", indicators), ("가격", prices)]:
    if frame.empty:
        raise ValueError(f"{name} 파일이 비어 있습니다.")

    if not frame["stock_code"].eq("005930").all():
        raise ValueError(f"{name} 파일의 종목코드를 확인해야 합니다.")

    if not frame["market"].eq("KRX").all():
        raise ValueError(f"{name} 파일의 시장을 확인해야 합니다.")

    frame["date"] = pd.to_datetime(
        frame["date"], format="%Y-%m-%d", errors="raise"
    )
    if frame["date"].isna().any() or frame["date"].duplicated().any():
        raise ValueError(f"{name} 파일에 날짜 결측 또는 중복이 있습니다.")

# 파일 사이에 날짜가 빠졌다면 임의로 삭제하거나 채우지 않습니다.
if set(indicators["date"]) != set(prices["date"]):
    raise ValueError("지표 파일과 가격 파일의 날짜 집합이 다릅니다.")

# merge는 종목코드와 날짜가 같은 행을 연결합니다.
# validate는 양쪽에서 연결 키가 한 번씩만 등장하는지 검사합니다.
table = indicators[["stock_code", "date", "ma_5", "ma_20"]].merge(
    prices[["stock_code", "date", "open"]],
    on=["stock_code", "date"],
    how="left",
    validate="one_to_one",
)
table = table.sort_values("date").reset_index(drop=True)

for column in ["ma_5", "ma_20", "open"]:
    table[column] = pd.to_numeric(table[column], errors="raise")
    if table[column].isin([float("inf"), float("-inf")]).any():
        raise ValueError(f"{column}에 무한대가 있습니다.")

if table["open"].isna().any() or table["open"].le(0).any():
    raise ValueError("시가에 결측값 또는 0 이하 값이 있습니다.")

# 지난 실습에서 확인한 초기 결측 구간 이후에 결측이 없어야 합니다.
for column, initial_missing in [("ma_5", 4), ("ma_20", 19)]:
    if (
        len(table) <= initial_missing
        or not table[column].iloc[:initial_missing].isna().all()
        or table[column].iloc[initial_missing:].isna().any()
    ):
        raise ValueError(f"{column}의 결측 구간을 확인해야 합니다.")

# 오늘과 이전 거래일의 이동평균을 비교합니다.
previous_5 = table["ma_5"].shift(1)
previous_20 = table["ma_20"].shift(1)

valid = (
    table["ma_5"].notna()
    & table["ma_20"].notna()
    & previous_5.notna()
    & previous_20.notna()
)
golden = valid & (previous_5 <= previous_20) & (
    table["ma_5"] > table["ma_20"]
)
dead = valid & (previous_5 >= previous_20) & (
    table["ma_5"] < table["ma_20"]
)

table["close_signal"] = "없음"
table.loc[golden, "close_signal"] = "골든크로스"
table.loc[dead, "close_signal"] = "데드크로스"

# 오늘 시가의 주문 판단에는 전날 마감 신호만 사용합니다.
table["previous_signal"] = table["close_signal"].shift(
    1, fill_value="없음"
)
table["previous_date"] = table["date"].shift(1)

holding = False
actions = []
states = []
order_rows = []

for row in table.itertuples(index=False):
    action = "없음"

    if row.previous_signal == "골든크로스" and not holding:
        action = "매수"
        holding = True
    elif row.previous_signal == "데드크로스" and holding:
        action = "매도"
        holding = False

    if action != "없음":
        # 신호 날짜는 모의 주문일보다 반드시 앞서야 합니다.
        if pd.isna(row.previous_date) or row.previous_date >= row.date:
            raise ValueError("신호 날짜와 모의 주문일의 순서가 잘못됐습니다.")

        order_rows.append({
            "stock_code": row.stock_code,
            "signal_date": row.previous_date,
            "order_date": row.date,
            "signal": row.previous_signal,
            "action": action,
            "assumed_open_price": row.open,
        })

    actions.append(action)
    states.append("보유" if holding else "미보유")

# 보유 상태는 다음 거래일 시가 체결을 가정한 모의 상태입니다.
table["open_order"] = actions
table["state_after_open"] = states

# 주문이 없어도 열 이름을 유지하도록 columns를 지정합니다.
order_columns = [
    "stock_code", "signal_date", "order_date",
    "signal", "action", "assumed_open_price",
]
orders = pd.DataFrame(order_rows, columns=order_columns)

# 미보유로 시작하고 추가 매수·공매도를 하지 않으므로 매수·매도가 교대합니다.
expected_action = "매수"
for action in orders["action"]:
    if action != expected_action:
        raise ValueError("모의 매수·매도 순서가 규칙과 다릅니다.")
    expected_action = "매도" if action == "매수" else "매수"

# 마지막 날 신호는 다음 행이 없으므로 주문으로 옮겨지지 않습니다.
# 남은 보유분을 임의로 강제 청산하지 않습니다.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
table.to_csv(SIGNAL_PATH, index=False, na_rep="")
orders.to_csv(ORDER_PATH, index=False)

print(f"전체 행 수: {len(table)}")
print(f"골든크로스: {golden.sum()}회")
print(f"데드크로스: {dead.sum()}회")
print(f"모의 매수: {orders['action'].eq('매수').sum()}회")
print(f"모의 매도: {orders['action'].eq('매도').sum()}회")
print(f"마지막 시가 처리 후 상태: {states[-1]}")
print(f"마지막 날 마감 신호: {table['close_signal'].iloc[-1]}")
print("마지막 날 마감 신호는 다음 거래일 데이터가 없어 체결하지 않음")

print("\n모의 주문 목록:")
if orders.empty:
    print("없음")
else:
    display = orders.rename(columns={
        "signal_date": "신호확인일",
        "order_date": "모의주문일",
        "signal": "전날신호",
        "action": "행동",
        "assumed_open_price": "가정한시가",
    })
    print(display.drop(columns="stock_code").to_string(index=False))

print("\n날짜 연결·주문 순서 검사: 통과")
print("실제 API 요청·주문: 없음")
print(f"전체 신호 저장: {SIGNAL_PATH}")
print(f"모의 주문 저장: {ORDER_PATH}")