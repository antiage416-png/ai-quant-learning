# 목적: 미체결 주문의 취소와 실제 모의 체결에 따른 계좌 변화를 검증합니다.
# 입력: 인위적인 거래 가능 상태와 44일차의 자금·비용 설정 및 예제 가격입니다.
# 처리: 전날 신호와 실제 모의 보유수량으로 주문을 정하고, 체결된 경우만 잔액을 바꿉니다.
# 결과: 매수 취소·매도 취소 예제와 현금·수량·비용 검증 결과를 출력합니다.
# 거래정지 표시는 가상 상황이며 실제 삼성전자 거래정지 기록이 아닙니다.
# 기존 설정과 계산 코드를 읽기만 합니다. 파일 저장·인터넷 요청·실제 주문은 없습니다.

import sys
from decimal import Decimal
from pathlib import Path

# pandas는 검증한 기록을 표로 출력하는 데 사용합니다.
import pandas as pd


# 폴더 이름에 하이픈이 있으므로 44일차 폴더를 모듈 검색 경로에 추가합니다.
# check_costs는 직접 실행할 때만 예제를 돌리므로 가져올 때 결과를 저장하지 않습니다.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "exercises" / "costs-day44"))
from check_costs import calculate_trade, load_settings, maximum_buy_quantity


# 전날 신호와 현재 보유수량을 받아 이번 시가의 주문 행동을 반환합니다.
# 매수 취소 후에는 주식이 없으므로 이후 데드크로스만으로 매도하지 않습니다.
def choose_action(previous_signal, shares):
    if previous_signal not in {"없음", "골든크로스", "데드크로스"}:
        raise ValueError("확인할 수 없는 신호입니다.")
    if previous_signal == "골든크로스" and shares == 0:
        return "매수"
    if previous_signal == "데드크로스" and shares > 0:
        return "매도"
    return "없음"


# 한 거래일의 시가 처리를 맡습니다. availability는 예제에서 명시한 상황입니다.
# 시가나 거래량으로 거래정지 여부를 추정하는 함수가 아닙니다.
# 반환하는 기록에는 이번 처리 후 현금·보유수량과 체결 여부가 들어 있습니다.
def process_open(previous_signal, cash, shares, availability, base_open, settings):
    if not cash.is_finite() or cash < 0 or not isinstance(shares, int) or shares < 0:
        raise ValueError("현금과 보유수량이 잘못되었습니다.")
    allowed = {"정상", "거래정지 확인", "시가 체결 불가 확인", "자료 미확인"}
    if availability not in allowed or availability == "자료 미확인":
        # 자료가 부족한 것과 체결 불가가 확인된 것은 다른 상황입니다.
        raise ValueError("자료가 확인되지 않아 계산을 중단합니다.")

    # 정상 상황에서는 기존 시가 전량 체결 가정을 유지합니다.
    # 가격 오류를 거래정지나 미체결로 바꾸어 숨기지 않습니다.
    if availability == "정상":
        if not isinstance(base_open, Decimal) or not base_open.is_finite() or base_open <= 0:
            raise ValueError("정상 상황의 기준 시가가 유효하지 않습니다.")

    action = choose_action(previous_signal, shares)
    record = {
        "action": action, "status": "주문 없음", "reason": "신호와 보유상태에 따른 주문 없음",
        "filled": False, "quantity": 0, "commission": Decimal("0"),
        "tax": Decimal("0"), "slippage_amount": Decimal("0"),
        "cash_before": cash, "cash_after": cash,
        "shares_before": shares, "shares_after": shares,
    }
    if action == "없음":
        return record

    if availability != "정상":
        # 합의한 취소 규칙: 체결 기록을 만들지 않고 주문을 종료합니다.
        # 현금·수량·비용은 위의 초기값을 유지합니다. 재주문 대기 상태는 만들지 않습니다.
        record.update(status="미체결 취소", reason=availability)
        return record

    # 가격·수수료·세금·슬리피지는 44일차 함수와 설정을 그대로 사용합니다.
    if action == "매수":
        price = base_open * (Decimal("1") + settings["slippage_rate"])
        quantity = maximum_buy_quantity(cash, price, settings["buy_commission_rate"])
        if quantity == 0:
            # 한 주도 살 수 없을 때 계산을 중단하는 기존 44일차 동작을 유지합니다.
            raise ValueError("비용을 포함해 한 주도 매수할 수 없습니다.")
    else:
        quantity = shares
    trade = calculate_trade(base_open, quantity, action, settings)
    change = quantity if action == "매수" else -quantity
    record.update(
        status="모의체결 완료", reason="기존 시가 전량 체결 가정", filled=True,
        quantity=quantity, commission=trade["fee"], tax=trade["tax"],
        slippage_amount=trade["slippage_amount"],
        cash_after=cash + trade["cash_change"], shares_after=shares + change,
    )
    return record


# 거래일마다 전날 신호를 하나씩 받아 잔액을 이어 갑니다.
# 취소한 주문을 다음 행에 넘기지 않습니다. 새 신호만 새 주문을 만들 수 있습니다.
def run_case(events, settings):
    cash, shares = settings["initial_cash"], 0
    records, fills = [], []
    for label, previous_signal, availability, base_open in events:
        record = process_open(previous_signal, cash, shares, availability, base_open, settings)
        record["day"] = label
        records.append(record)
        if record["filled"]:
            fills.append(record)
        cash, shares = record["cash_after"], record["shares_after"]
    return records, fills


def show_case(title, records, fills):
    columns = ["day", "action", "status", "quantity", "cash_after", "shares_after", "commission", "tax"]
    names = {
        "day": "순서", "action": "주문", "status": "처리", "quantity": "체결수량",
        "cash_after": "처리후현금", "shares_after": "보유수량", "commission": "수수료", "tax": "세금",
    }
    print(f"\n[{title}]")
    display = pd.DataFrame(records)[columns].copy()
    # 표의 금액 표시만 정리합니다. 검증과 계산에 쓰는 원래 기록은 바꾸지 않습니다.
    display["cash_after"] = display["cash_after"].map(lambda value: f"{value:,.2f}")
    for column in ("commission", "tax"):
        display[column] = display[column].map(lambda value: f"{value:,.0f}")
    print(display.rename(columns=names).to_string(index=False))
    print(f"모의 체결 기록 수: {len(fills)}건")


def main():
    settings = load_settings()
    # 설정 변경으로 손계산 기준이 달라지지 않았는지 먼저 확인합니다.
    expected = {
        "initial_cash": Decimal("10000000"),
        "buy_commission_rate": Decimal("0.000140527"),
        "sell_commission_rate": Decimal("0.000140527"),
        "sell_tax_rate": Decimal("0.0015"),
        "slippage_rate": Decimal("0.0005"),
    }
    if settings != expected:
        raise ValueError("합의한 44일차 설정과 다릅니다.")

    # 날짜를 붙이지 않은 별도 가상 상황입니다. 가격은 기존 작은 예제에서 가져옵니다.
    # 취소된 매수는 다음 날 재주문하지 않고, 주식 없는 상태의 매도 신호도 주문을 만들지 않습니다.
    buy_case, buy_fills = run_case([
        ("첫날", "골든크로스", "거래정지 확인", None),
        ("둘째 날", "없음", "정상", Decimal("55100")),
        ("셋째 날", "데드크로스", "정상", Decimal("53300")),
    ], settings)
    assert buy_case[0]["status"] == "미체결 취소"
    assert all(row["cash_after"] == Decimal("10000000") and row["shares_after"] == 0 for row in buy_case)
    assert buy_case[1]["action"] == buy_case[2]["action"] == "없음"
    assert not buy_fills

    # 매도 취소 후에는 보유를 유지합니다. 이후 골든크로스에도 추가 매수하지 않습니다.
    # 마지막 날의 새 데드크로스는 그 사이 골든크로스를 거친 별도 신호입니다.
    sell_case, sell_fills = run_case([
        ("첫날", "골든크로스", "정상", Decimal("55100")),
        ("둘째 날", "데드크로스", "시가 체결 불가 확인", None),
        ("셋째 날", "없음", "정상", Decimal("53300")),
        ("넷째 날", "골든크로스", "정상", Decimal("55100")),
        ("다섯째 날", "데드크로스", "정상", Decimal("53300")),
    ], settings)
    assert sell_case[0]["shares_after"] == 181
    assert sell_case[0]["cash_after"] == Decimal("20511.45")
    assert sell_case[1]["status"] == "미체결 취소"
    assert sell_case[2]["action"] == sell_case[3]["action"] == "없음"
    assert all(sell_case[index]["cash_after"] == Decimal("20511.45") and sell_case[index]["shares_after"] == 181 for index in (1, 2, 3))
    assert sell_case[-1]["cash_after"] == Decimal("9647169.80")
    assert sell_case[-1]["shares_after"] == 0 and len(sell_fills) == 2

    # 체결이 없었던 모든 행에서 잔액과 체결 비용이 그대로인지 검사합니다.
    for row in buy_case + sell_case:
        if not row["filled"]:
            assert row["cash_after"] == row["cash_before"]
            assert row["shares_after"] == row["shares_before"]
            assert row["quantity"] == 0
            assert row["commission"] == row["tax"] == row["slippage_amount"] == 0

    # 확인되지 않은 자료와 잘못된 가격은 취소 처리로 숨기지 않고 계산을 중단합니다.
    invalid = [
        ("자료 미확인", "자료 미확인", None),
        ("시가 0", "정상", Decimal("0")),
        ("시가 결측", "정상", None),
        ("시가 무한대", "정상", Decimal("Infinity")),
    ]
    for label, availability, price in invalid:
        try:
            process_open("골든크로스", settings["initial_cash"], 0, availability, price, settings)
        except ValueError:
            print(f"{label} 계산 중단 검사: 통과")
        else:
            raise AssertionError(f"잘못된 자료를 통과시켰습니다: {label}")

    show_case("매수 취소 예제", buy_case, buy_fills)
    show_case("매도 취소 예제", sell_case, sell_fills)
    print("\n미체결 현금·수량·체결비용 불변 검사: 통과")
    print("취소 주문 다음 날 자동 재주문 없음 검사: 통과")
    print("미보유 매도 차단 검사: 통과")
    print("보유 중 추가 매수 차단 검사: 통과")
    print("새 신호에 따른 정상 체결·44일차 손계산 비교: 통과")
    print("실제 API 요청·주문·결과 파일 저장: 없음")


if __name__ == "__main__":
    main()
