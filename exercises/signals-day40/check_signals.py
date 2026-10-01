# 목적: 교차를 판단한 날짜와 다음 거래일 주문 예정 날짜를 구분합니다.
# 입력: 검증용 이동평균 예제
# 처리: 이전 값 비교 → 교차 신호 → 다음 행에 주문 후보 배치
# 출력: 비교 표와 검증 결과
# 실제 주문, API 요청, 파일 저장은 없습니다.

import pandas as pd


def detect_crosses(ma_5, ma_20):
    # shift(1)은 이전 행의 값을 현재 행으로 가져옵니다.
    previous_5 = ma_5.shift(1)
    previous_20 = ma_20.shift(1)

    # 이전·오늘의 두 평균이 모두 있어야 교차를 판단합니다.
    valid = (
        ma_5.notna()
        & ma_20.notna()
        & previous_5.notna()
        & previous_20.notna()
    )

    # &는 각 행에서 양쪽 조건이 모두 참인지 확인합니다.
    golden = valid & (previous_5 <= previous_20) & (ma_5 > ma_20)
    dead = valid & (previous_5 >= previous_20) & (ma_5 < ma_20)

    # 신호를 문자열로 표시합니다. 교차가 없으면 "없음"입니다.
    signal = pd.Series("없음", index=ma_5.index, dtype="string")
    signal.loc[golden] = "골든크로스"
    signal.loc[dead] = "데드크로스"
    return signal


table = pd.DataFrame({
    "date": pd.to_datetime([
        "2025-01-06",
        "2025-01-07",
        "2025-01-08",
        "2025-01-09",
        "2025-01-10",
    ]),
    "ma_5": [99.0, 101.0, 102.0, 99.0, 98.0],
    "ma_20": [100.0, 100.0, 100.0, 100.0, 100.0],
})

table["close_signal"] = detect_crosses(table["ma_5"], table["ma_20"])

# 전날 장 마감에 확정된 교차 신호를 다음 행으로 옮깁니다.
# shift(1)은 다음 달력 날짜가 아니라 데이터의 다음 거래일에 연결합니다.
table["previous_signal"] = table["close_signal"].shift(
    1, fill_value="없음"
)

# 실제 데이터 구현 전, 보유 상태에 따라 주문 후보를 걸러냅니다.
# 이 예제에서는 주문 예정일 시가에 체결된다고 가정해 상태만 갱신합니다.
# 수량·금액·체결 가격·수익률은 계산하지 않습니다.
holding = False
orders = []
states = []

for previous_signal in table["previous_signal"]:
    order = "없음"

    if previous_signal == "골든크로스" and not holding:
        order = "매수"
        holding = True
    elif previous_signal == "데드크로스" and holding:
        order = "매도"
        holding = False

    orders.append(order)
    states.append("보유" if holding else "미보유")

table["open_order"] = orders
table["state_after_open"] = states

# 신호 발생일과 주문 예정일을 각각 확인합니다.
expected_signals = [
    "없음", "골든크로스", "없음", "데드크로스", "없음"
]
expected_orders = ["없음", "없음", "매수", "없음", "매도"]

if table["close_signal"].tolist() != expected_signals:
    raise ValueError("교차 신호 발생일이 예상과 다릅니다.")

if table["open_order"].tolist() != expected_orders:
    raise ValueError("다음 거래일 주문 배치가 예상과 다릅니다.")

# 동률에 머문 날에는 신호가 없고, 동률에서 벗어난 날에 판단합니다.
equal_test = detect_crosses(
    pd.Series([99.0, 100.0, 101.0, 100.0, 99.0]),
    pd.Series([100.0] * 5),
)
if equal_test.tolist() != [
    "없음", "없음", "골든크로스", "없음", "데드크로스"
]:
    raise ValueError("동률 처리 결과가 규칙과 다릅니다.")

# 처음 유효해진 평균이 이미 위에 있어도 새 교차로 간주하지 않습니다.
missing_test = detect_crosses(
    pd.Series([float("nan"), 101.0, 102.0]),
    pd.Series([100.0, 100.0, 100.0]),
)
if missing_test.ne("없음").any():
    raise ValueError("이전 값이 없는데 교차가 생성됐습니다.")

# 화면에는 의미가 드러나도록 한국어 열 이름을 붙입니다.
display = table.rename(columns={
    "date": "거래일",
    "ma_5": "5일평균",
    "ma_20": "20일평균",
    "close_signal": "당일마감신호",
    "open_order": "당일시가주문",
    "state_after_open": "시가처리후상태",
})

print(display[[
    "거래일", "5일평균", "20일평균",
    "당일마감신호", "당일시가주문", "시가처리후상태",
]].to_string(index=False))

print("\n교차 발생일 검사: 통과")
print("다음 거래일 주문 배치 검사: 통과")
print("동률 처리 검사: 통과")
print("초기 결측 처리 검사: 통과")
print("실제 API 요청·주문: 없음")

