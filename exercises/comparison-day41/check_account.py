# 목적: 정수 수량 매수·잔액 유지·전량 매도 계산을 검증합니다.
# 입력: 초기자금 1,000만원과 검증용 가격·행동 3개
# 처리: 시가 거래 → 현금·수량 갱신 → 종가로 자산 평가
# 출력: 계산 표와 손계산 비교 결과
# 비용·배당·현금 이자는 제외합니다.
# 실제 주문·API 요청·파일 저장은 없습니다.

from math import isclose

import pandas as pd


INITIAL_CASH = 10_000_000

example = pd.DataFrame({
    "순서": ["첫날", "둘째 날", "셋째 날"],
    "행동": ["매수", "유지", "매도"],
    "시가": [55_100, 56_000, 53_300],
    "종가": [55_900, 54_000, 53_900],
})

cash = INITIAL_CASH
shares = 0
records = []

for _, row in example.iterrows():
    open_price = int(row["시가"])
    close_price = int(row["종가"])
    action = row["행동"]
    traded_shares = 0

    if action == "매수":
        if shares != 0:
            raise ValueError("보유 중 추가 매수는 허용하지 않습니다.")

        # //는 나눗셈 결과의 정수 몫을 구합니다.
        # 현금으로 살 수 있는 최대 정수 수량을 계산합니다.
        traded_shares = cash // open_price
        cash -= traded_shares * open_price
        shares = traded_shares

    elif action == "매도":
        if shares == 0:
            raise ValueError("미보유 상태에서는 매도할 수 없습니다.")

        # 보유 수량 전부를 시가로 매도해 현금으로 바꿉니다.
        traded_shares = shares
        cash += shares * open_price
        shares = 0

    elif action != "유지":
        raise ValueError("정의되지 않은 행동입니다.")

    if cash < 0 or shares < 0:
        raise ValueError("현금이나 보유 수량이 음수가 됐습니다.")

    # 거래 처리 이후의 수량을 당일 종가로 평가합니다.
    equity = cash + shares * close_price

    records.append({
        "순서": row["순서"],
        "행동": action,
        "거래수량": traded_shares,
        "남은현금": cash,
        "보유수량": shares,
        "종가평가자산": equity,
    })

result = pd.DataFrame(records)

# 가격·현금·수량은 정수이므로 손계산 값과 정확히 비교합니다.
expected_values = {
    "거래수량": [181, 0, 181],
    "남은현금": [26_900, 26_900, 9_674_200],
    "보유수량": [181, 181, 0],
    "종가평가자산": [10_144_800, 9_800_900, 9_674_200],
}

for column, expected in expected_values.items():
    if result[column].tolist() != expected:
        raise ValueError(f"{column}이 손계산 결과와 다릅니다.")

# 초기자금 대비 최종 손익과 수익률을 계산합니다.
final_equity = int(result["종가평가자산"].iloc[-1])
profit = final_equity - INITIAL_CASH
total_return = final_equity / INITIAL_CASH - 1

if profit != -325_800:
    raise ValueError("최종 손익이 손계산과 다릅니다.")

# 소수 수익률은 작은 계산 오차를 허용해 비교합니다.
if not isclose(total_return, -0.03258, rel_tol=1e-9, abs_tol=1e-12):
    raise ValueError("최종 수익률이 손계산과 다릅니다.")

print(result.to_string(index=False))
print(f"\n초기자금: {INITIAL_CASH:,.0f}원")
print(f"최종 자산가치: {final_equity:,.0f}원")
print(f"최종 손익: {profit:,.0f}원")
print(f"비용 차감 전 수익률: {total_return:.4%}")
print("현금·수량·자산가치 손계산 비교: 통과")
print("최종 손익·수익률 비교: 통과")