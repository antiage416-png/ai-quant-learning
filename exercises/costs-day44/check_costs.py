# 목적: 설정파일의 비용을 읽고 작은 매매 예제를 손계산과 비교합니다.
# 실행 중에는 설정파일만 읽으며 파일 저장이나 인터넷 요청은 없습니다.
import json
from decimal import Decimal, ROUND_DOWN
from pathlib import Path


# Decimal은 문자열에서 정확한 십진수를 만들어 금액 계산에 사용합니다.
def load_settings():
    path = Path(__file__).resolve().parent / "cost_settings.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    keys = (
        "initial_cash", "buy_commission_rate", "sell_commission_rate",
        "sell_tax_rate", "slippage_rate",
    )
    settings = {key: Decimal(raw[key]) for key in keys}
    if any(not value.is_finite() for value in settings.values()):
        raise ValueError("자금과 비용 설정은 유한한 숫자여야 합니다.")
    if settings["initial_cash"] <= 0:
        raise ValueError("초기 자금은 양수여야 합니다.")
    for key in keys[1:]:
        if not Decimal("0") <= settings[key] < Decimal("1"):
            raise ValueError(f"비용률 범위가 잘못되었습니다: {key}")
    return settings


# 양수인 수수료와 세금에서 1원 미만을 버립니다.
def floor_won(value):
    return value.quantize(Decimal("1"), rounding=ROUND_DOWN)


# 가격으로 살 수 있는 수량부터 시작해 수수료까지 감당할 때까지 줄입니다.
# 반환한 수량보다 한 주 더 사면 예산을 초과하므로 최대 정수 수량입니다.
def maximum_buy_quantity(cash, price, rate):
    if cash < 0 or price <= 0:
        raise ValueError("현금은 음수가 아니어야 하고 가격은 양수여야 합니다.")
    quantity = int(cash // price)
    while quantity > 0:
        amount = price * quantity
        if amount + floor_won(amount * rate) <= cash:
            return quantity
        quantity -= 1
    return 0


# 기준 시가에 슬리피지를 반영하고 체결금액·비용·현금변화를 반환합니다.
# 슬리피지 환산액은 설명용이며 현금에서 다시 차감하지 않습니다.
def calculate_trade(base_price, quantity, action, settings):
    if action not in {"매수", "매도"}:
        raise ValueError("행동은 매수 또는 매도여야 합니다.")
    if base_price <= 0 or not isinstance(quantity, int) or quantity < 0:
        raise ValueError("가격은 양수이고 수량은 음수가 아닌 정수여야 합니다.")
    direction = Decimal("1") if action == "매수" else Decimal("-1")
    price = base_price * (Decimal("1") + direction * settings["slippage_rate"])
    amount = price * quantity
    rate_key = "buy_commission_rate" if action == "매수" else "sell_commission_rate"
    fee = floor_won(amount * settings[rate_key])
    tax = floor_won(amount * settings["sell_tax_rate"]) if action == "매도" else Decimal("0")
    cash_change = -amount - fee if action == "매수" else amount - fee - tax
    return {
        "price": price, "amount": amount, "fee": fee, "tax": tax,
        "slippage_amount": abs(price - base_price) * quantity,
        "cash_change": cash_change,
    }


def main():
    settings = load_settings()
    initial_cash = settings["initial_cash"]

    # 손계산은 합의한 1,000만원과 비용 설정을 기준으로 합니다.
    expected = {
        "initial_cash": Decimal("10000000"),
        "buy_commission_rate": Decimal("0.000140527"),
        "sell_commission_rate": Decimal("0.000140527"),
        "sell_tax_rate": Decimal("0.0015"),
        "slippage_rate": Decimal("0.0005"),
    }
    if settings != expected:
        raise ValueError("합의한 설정과 다릅니다. 설정 변경 시 손계산 기준도 새로 정해야 합니다.")

    cash = initial_cash
    shares = 0

    # 첫날 시가 55,100원에 비용을 포함해 최대 수량을 매수합니다.
    buy_open = Decimal("55100")
    buy_price = buy_open * (Decimal("1") + settings["slippage_rate"])
    quantity = maximum_buy_quantity(cash, buy_price, settings["buy_commission_rate"])
    buy = calculate_trade(buy_open, quantity, "매수", settings)
    cash += buy["cash_change"]
    shares += quantity
    buy_cash = cash
    buy_equity = cash + shares * Decimal("55900")
    hold_equity = cash + shares * Decimal("54000")

    # 셋째 날 시가 53,300원을 기준으로 전량 매도합니다.
    sell_quantity = shares
    sell = calculate_trade(Decimal("53300"), sell_quantity, "매도", settings)
    cash += sell["cash_change"]
    shares -= sell_quantity
    final_cash = cash
    final_quantity = shares
    profit = final_cash - initial_cash
    final_return = final_cash / initial_cash - Decimal("1")

    # 소수 가격·비용 버림·현금·종가 평가를 각각 독립 손계산과 비교합니다.
    assert quantity == 181
    assert buy["price"] == Decimal("55127.55")
    assert buy["amount"] == Decimal("9978086.55")
    assert buy["fee"] == Decimal("1402") and buy["tax"] == 0
    assert buy_cash == Decimal("20511.45")
    assert buy_equity == Decimal("10138411.45")
    assert hold_equity == Decimal("9794511.45")
    assert sell["price"] == Decimal("53273.35")
    assert sell["amount"] == Decimal("9642476.35")
    assert sell["fee"] == Decimal("1355") and sell["tax"] == Decimal("14463")
    assert buy["slippage_amount"] + sell["slippage_amount"] == Decimal("9810.20")
    assert final_cash == Decimal("9647169.80") and final_quantity == 0
    assert final_return == Decimal("-0.03528302")
    next_buy = calculate_trade(buy_open, quantity + 1, "매수", settings)
    assert next_buy["amount"] + next_buy["fee"] > initial_cash

    # 시가 10만원·슬리피지0인 별도 예제에서는 수수료 때문에 99주만 삽니다.
    boundary_price = Decimal("100000")
    boundary_rate = settings["buy_commission_rate"]
    boundary_quantity = maximum_buy_quantity(initial_cash, boundary_price, boundary_rate)
    assert boundary_quantity == 99
    assert floor_won(boundary_price * boundary_quantity * boundary_rate) == Decimal("1391")

    # 비용을 버리기 전의 값으로 수량을 줄이지 않는지도 확인합니다.
    
    assert maximum_buy_quantity(Decimal("100014"), boundary_price, boundary_rate) == 1
    assert maximum_buy_quantity(initial_cash, boundary_price, Decimal("0")) == 100

    print("작은 예제의 비용 적용 결과:")
    print(f"매수 수량: {quantity}주")
    print(f"매수 가정가격: {buy['price']:,.2f}원")
    print(f"매수 수수료: {buy['fee']:,.0f}원 / 매수 후 현금: {buy_cash:,.2f}원")
    print(f"첫날 종가 평가 자산: {buy_equity:,.2f}원")
    print(f"둘째 날 종가 평가 자산: {hold_equity:,.2f}원")
    print(f"매도 가정가격: {sell['price']:,.2f}원")
    print(f"매도 수수료: {sell['fee']:,.0f}원 / 매도 세금: {sell['tax']:,.0f}원")
    print(f"최종 현금: {final_cash:,.2f}원 / 최종 보유수량: {final_quantity}주")
    print(f"최종 손익: {profit:,.2f}원 / 수익률: {final_return * 100:.6f}%")
    print(f"수수료 포함 경계 예제: 비용 없을 때 100주 / 비용 포함 {boundary_quantity}주")
    print("현금·수량·가격·비용 손계산 비교: 통과")
    print("최대 매수수량·비용 버림 경계 검사: 통과")
    print("실제 API 요청·주문·결과 파일 저장: 없음")


# 직접 실행할 때만 예제를 돌립니다. 다음 실습에서는 계산 함수만 가져옵니다.
if __name__ == "__main__":
    main()