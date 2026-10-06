# 목적: 거래 전 계좌의 현금과 보유수량을 확인합니다.
# 입력 → 처리 → 결과: 초기 자금 → 계좌 상태 설정 → 화면 출력.
# 파일 저장이나 인터넷 요청은 없습니다.

# 초기 자금은 이후 수익률 비교에 사용할 기준값입니다.
initial_cash = 10_000_000

# 현재 현금과 보유수량은 거래할 때마다 바뀌는 값입니다.
cash = initial_cash
shares = 0

# 쉼표로 천 단위를 구분해 계좌 상태를 출력합니다.
print(f"초기 자금: {initial_cash:,}원")
print(f"현재 현금: {cash:,}원")
print(f"보유수량: {shares}주")

# Decimal은 가격과 비용 비율을 십진수로 계산하는 데 사용합니다.
from decimal import Decimal

# 앞서 사용한 작은 예제의 시가와 기존 비용 조건을 유지합니다.
opening_price = Decimal("55100")
slippage_rate = Decimal("0.0005")       # 0.05%를 소수로 표현합니다.
commission_rate = Decimal("0.000140527")  # 수수료 0.0140527%입니다.

# 매수는 기준 시가보다 불리한 방향, 즉 더 높은 가격을 가정합니다.
buy_price = opening_price * (Decimal("1") + slippage_rate)

# :.2f는 소수점 아래 두 자리까지 표시하며 변수 자체를 바꾸지는 않습니다.
print(f"기준 시가: {opening_price:,.2f}원")
print(f"매수 가정가격: {buy_price:,.2f}원")

# 현재 현금을 소수 금액 계산에 사용할 Decimal로 변환합니다.
cash = Decimal(cash)

# 현금을 1주 가격으로 나누고 소수 부분을 버려 정수 수량을 구합니다.
# 현금과 가격이 양수이므로 int()를 사용하면 살 수 있는 온전한 주 수가 됩니다.
buy_quantity = int(cash / buy_price)

# 수수료를 제외한 체결금액과 그 금액을 지불한 뒤 남을 현금을 계산합니다.
trade_amount = buy_price * buy_quantity
cash_before_fee = cash - trade_amount

print(f"수수료 반영 전 매수 가능 수량: {buy_quantity}주")
print(f"매수 체결금액: {trade_amount:,.2f}원")
print(f"수수료 차감 전 남을 현금: {cash_before_fee:,.2f}원")

# 수수료는 슬리피지가 반영된 체결금액을 기준으로 계산합니다.
fee_before_rounding = trade_amount * commission_rate

# 수수료가 양수이므로 int()로 소수 부분을 버리면 원 미만 버림이 됩니다.
buy_fee = Decimal(int(fee_before_rounding))

# 실제 매수에 필요한 금액은 체결금액과 수수료의 합입니다.
total_payment = trade_amount + buy_fee

# <=는 왼쪽 값이 오른쪽 값 이하인지 판단해 True 또는 False를 만듭니다.
can_buy = total_payment <= cash

print(f"매수 수수료: {buy_fee:,.0f}원")
print(f"수수료 포함 필요 금액: {total_payment:,.2f}원")
print(f"현재 현금으로 매수 가능: {can_buy}")

# 현금이 충분할 때만 모의 매수를 계좌에 반영합니다.
if can_buy:
    # 총 필요 금액에는 수수료가 포함되어 있으므로 다시 빼지 않습니다.
    cash = cash - total_payment
    shares = shares + buy_quantity

    print(f"매수 후 현금: {cash:,.2f}원")
    print(f"매수 후 보유수량: {shares}주")
else:
    # 현금이 부족하면 계좌를 변경하지 않습니다.
    print("현금이 부족합니다. 매수수량을 줄여 다시 계산해야 합니다.")

# 손으로 계산한 기대값과 실제 계좌 상태를 비교합니다.
# assert는 조건이 맞으면 계속 진행하고, 틀리면 오류를 내며 중단합니다.
assert cash == Decimal("20511.45"), "매수 후 현금이 손계산과 다릅니다."
assert shares == 181, "매수 후 보유수량이 손계산과 다릅니다."

# 매수 후 현금 + 주식 매수에 쓴 금액 + 수수료 = 초기 자금이어야 합니다.
assert cash + trade_amount + buy_fee == initial_cash, "매수 전후 금액이 맞지 않습니다."

print("매수 후 현금·수량 손계산 비교: 통과")
print("초기 자금과 매수 지출·잔액 대조: 통과")

# 기존 작은 예제의 매도 시가와 합의한 매도 세금 비율을 사용합니다.
sell_opening_price = Decimal("53300")
sell_tax_rate = Decimal("0.0015")  # 기존 실습의 2025년 매도 세금 0.15%입니다.

# 매도는 기준 시가보다 낮은 가격으로 체결된다고 가정합니다.
sell_price = sell_opening_price * (Decimal("1") - slippage_rate)

# 현재 보유한 주식을 전부 매도할 때의 금액을 계산합니다.
sell_quantity = shares
sell_amount = sell_price * sell_quantity

# 수수료와 세금은 각각 계산하고 각각 원 미만을 버립니다.
sell_fee = Decimal(int(sell_amount * commission_rate))
sell_tax = Decimal(int(sell_amount * sell_tax_rate))

# 매도금액에서 비용을 뺀 나머지가 계좌에 들어올 금액입니다.
sell_proceeds = sell_amount - sell_fee - sell_tax

print(f"매도 가정가격: {sell_price:,.2f}원")
print(f"매도수량: {sell_quantity}주")
print(f"매도 체결금액: {sell_amount:,.2f}원")
print(f"매도 수수료: {sell_fee:,.0f}원")
print(f"매도 세금: {sell_tax:,.0f}원")
print(f"매도 후 들어올 금액: {sell_proceeds:,.2f}원")

# 보유수량보다 많이 팔거나 0주를 매도하는 잘못된 처리를 차단합니다.
assert 0 < sell_quantity <= shares, "매도수량을 확인해야 합니다."

# 수수료와 세금이 이미 차감된 입금액을 더하므로 비용을 다시 빼지 않습니다.
cash = cash + sell_proceeds
shares = shares - sell_quantity

print(f"매도 후 현금: {cash:,.2f}원")
print(f"매도 후 보유수량: {shares}주")

# 전량 매도 후의 계좌 상태를 손계산 결과와 비교합니다.
assert cash == Decimal("9647169.80"), "매도 후 현금이 손계산과 다릅니다."
assert shares == 0, "전량 매도 후 보유수량이 0주가 아닙니다."

print("매도 후 현금·수량 손계산 비교: 통과")

# 전량 매도한 상태에서만 현금을 최종 자산으로 사용합니다.
assert shares == 0, "주식이 남아 있으면 주식 평가금액도 더해야 합니다."
final_equity = cash

# 초기 자금 대비 손익과 수익률을 계산합니다.
profit = final_equity - initial_cash
return_rate = profit / initial_cash

# 수익률은 소수로 보관하고, 출력할 때만 100을 곱해 퍼센트로 표시합니다.
print(f"최종 자산: {final_equity:,.2f}원")
print(f"최종 손익: {profit:,.2f}원")
print(f"최종 수익률: {return_rate * 100:.6f}%")

# 손계산한 손익과 수익률을 정확히 비교합니다.
assert profit == Decimal("-352830.20"), "손익이 손계산과 다릅니다."
assert return_rate == Decimal("-0.03528302"), "수익률이 손계산과 다릅니다."

print("최종 손익·수익률 손계산 비교: 통과")

# 별도 예제: 수수료 때문에 매수수량을 줄여야 하는 경우를 확인합니다.
example_cash = Decimal("10000")
example_price = Decimal("100")  # 슬리피지가 이미 반영된 1주 가격입니다.

# 우선 수수료를 제외하고 살 수 있는 정수 수량부터 시작합니다.
example_quantity = int(example_cash / example_price)

# 수량이 남아 있는 동안 비용을 계산하고 매수 가능한지 확인합니다.
while example_quantity > 0:
    example_amount = example_price * example_quantity
    example_fee = Decimal(int(example_amount * commission_rate))
    example_payment = example_amount + example_fee

    print(f"{example_quantity}주 매수에 필요한 금액: {example_payment:,.0f}원")

    # 현금으로 감당할 수 있으면 수량을 확정하고 반복을 끝냅니다.
    if example_payment <= example_cash:
        break

    # 현금이 부족하면 1주 줄인 뒤 반복문의 처음으로 돌아갑니다.
    example_quantity = example_quantity - 1

print(f"수수료를 포함한 매수 가능 수량: {example_quantity}주")

# 이번 예제에서 매수 가능한 수량이 손계산과 일치하는지 확인합니다.
assert example_quantity == 99, "매수 가능 수량이 손계산과 다릅니다."

# 확정된 수량의 필요 금액과 남을 현금을 확인합니다.
example_remaining_cash = example_cash - example_payment

assert example_payment == Decimal("9901"), "총 필요 금액이 다릅니다."
assert example_remaining_cash == Decimal("99"), "남을 현금이 다릅니다."

print(f"예제 매수 후 남을 현금: {example_remaining_cash:,.0f}원")
print("수수료 포함 매수수량·잔액 검사: 통과")