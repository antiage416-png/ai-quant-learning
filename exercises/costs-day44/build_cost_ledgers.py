# 목적: 같은 기간·초기자금으로 두 전략의 비용 반영 장부와 비교 요약을 저장합니다.
# 기존 가격·신호·41일차 결과를 읽습니다. 인터넷 요청이나 실제 주문은 없습니다.
import json
from decimal import Decimal
from pathlib import Path

import pandas as pd

# 같은 폴더의 작은 예제에서 검증한 계산 함수를 가져옵니다.
# 가져오기만 할 때는 작은 예제가 실행되지 않습니다.
from check_costs import calculate_trade, load_settings, maximum_buy_quantity


ROOT = Path("/home/jaeho/ai-quant-learning")
HERE = Path(__file__).resolve().parent
CODE = "005930"
ZERO = Decimal("0")
ONE = Decimal("1")


# CSV의 종목코드·날짜·필수 열을 확인하고 날짜를 같은 형식으로 맞춥니다.
def read_input(path, required):
    frame = pd.read_csv(path, dtype={"stock_code": str})
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f"필수 열이 없습니다: {path.name}, {sorted(missing)}")
    if frame.empty or frame["stock_code"].isna().any():
        raise ValueError(f"빈 데이터 또는 빈 종목코드가 있습니다: {path.name}")
    if not frame["stock_code"].str.zfill(6).eq(CODE).all():
        raise ValueError(f"삼성전자 이외 종목이 있습니다: {path.name}")
    dates = pd.to_datetime(frame["date"], format="%Y-%m-%d", errors="raise")
    if dates.isna().any() or dates.duplicated().any() or not dates.is_monotonic_increasing:
        raise ValueError(f"날짜 결측·중복·순서 오류가 있습니다: {path.name}")
    if not dates.dt.year.eq(2025).all():
        raise ValueError(f"2025년 이외 날짜가 있습니다: {path.name}")
    frame["stock_code"] = CODE
    frame["date"] = dates.dt.strftime("%Y-%m-%d")
    return frame.reset_index(drop=True)


# 문자열을 정확한 십진수로 읽고 원본 시가·종가가 양수인지 확인합니다.
def read_price(value):
    result = Decimal(str(value))
    if not result.is_finite() or result <= ZERO:
        raise ValueError("시가와 종가는 유한한 양수여야 합니다.")
    return result


# 장부를 시간순으로 계산합니다. 매수 수량은 그날 현금과 비용으로 새로 정합니다.
def simulate(prices, actions, signal_dates, settings, strategy):
    cash = settings["initial_cash"]
    shares = 0
    peak = cash
    rows = []
    for row, action, signal_date in zip(prices.itertuples(index=False), actions, signal_dates):
        base_open = read_price(row.open)
        close = read_price(row.close)
        cash_before, shares_before = cash, shares
        quantity = 0
        trade = dict.fromkeys(
            ["price", "amount", "fee", "tax", "slippage_amount", "cash_change"], ZERO
        )
        if action == "매수":
            if shares != 0:
                raise ValueError(f"보유 중 추가 매수입니다: {strategy}, {row.date}")
            price = base_open * (ONE + settings["slippage_rate"])
            quantity = maximum_buy_quantity(cash, price, settings["buy_commission_rate"])
            if quantity == 0:
                raise ValueError(f"비용 포함 1주 매수가 불가능합니다: {strategy}, {row.date}")
            trade = calculate_trade(base_open, quantity, action, settings)
            shares += quantity
        elif action == "매도":
            if shares <= 0:
                raise ValueError(f"보유 주식 없는 매도입니다: {strategy}, {row.date}")
            quantity = shares
            trade = calculate_trade(base_open, quantity, action, settings)
            shares -= quantity
        elif action != "없음":
            raise ValueError(f"알 수 없는 행동입니다: {action}")

        cash += trade["cash_change"]
        if cash < ZERO or shares < 0:
            raise ValueError(f"음수 현금 또는 수량입니다: {strategy}, {row.date}")
        stock_value = shares * close
        equity = cash + stock_value
        peak = max(peak, equity)
        rows.append({
            "strategy": strategy, "stock_code": CODE, "date": row.date,
            "signal_date": signal_date, "action": action, "base_open": base_open,
            "fill_price": trade["price"], "traded_shares": quantity,
            "amount": trade["amount"], "commission": trade["fee"], "tax": trade["tax"],
            "slippage_amount": trade["slippage_amount"],
            "cash_before": cash_before, "cash_change": trade["cash_change"], "cash_after": cash,
            "shares_before": shares_before, "shares_change": shares - shares_before,
            "shares_after": shares, "close": close, "stock_value": stock_value, "equity": equity,
            "cumulative_return": equity / settings["initial_cash"] - ONE,
            "running_peak": peak, "drawdown": equity / peak - ONE,
        })
    return pd.DataFrame(rows)


# 비용 0의 결과가 41일차의 모든 거래일 결과와 같은지 확인합니다.
def check_baseline(frame, reference, prefix):
    for source, target in (
        ("cash_after", "cash"), ("shares_after", "shares"),
        ("equity", "equity"), ("traded_shares", "traded_shares"),
        ("running_peak", "running_peak"),
    ):
        actual = [Decimal(str(value)) for value in frame[source]]
        expected = [Decimal(str(value)) for value in reference[f"{prefix}_{target}"]]
        if actual != expected:
            raise ValueError(f"41일차 대조 실패: {prefix}, {target}")
    if frame["action"].tolist() != reference[f"{prefix}_action"].tolist():
        raise ValueError(f"41일차 행동 대조 실패: {prefix}")
    for column in ("cumulative_return", "drawdown"):
        for actual, expected in zip(frame[column], reference[f"{prefix}_{column}"]):
            if abs(actual - Decimal(str(expected))) > Decimal("0.000000000001"):
                raise ValueError(f"41일차 비율 대조 실패: {prefix}, {column}")


# 현금·수량의 연결과 체결금액·비용으로 재구성한 현금변화를 검사합니다.
def check_ledger(frame, initial_cash):
    cash, shares = initial_cash, 0
    for row in frame.itertuples(index=False):
        assert row.cash_before == cash and row.shares_before == shares
        if row.action == "매수":
            expected_change = -row.amount - row.commission
            expected_shares_change = row.traded_shares
            assert row.tax == ZERO
        elif row.action == "매도":
            expected_change = row.amount - row.commission - row.tax
            expected_shares_change = -row.traded_shares
        else:
            expected_change, expected_shares_change = ZERO, 0
            assert row.amount == row.commission == row.tax == row.slippage_amount == ZERO
        assert row.cash_change == expected_change
        assert row.shares_change == expected_shares_change
        assert row.cash_after == cash + expected_change
        assert row.shares_after == shares + expected_shares_change
        assert row.stock_value == row.shares_after * row.close
        assert row.equity == row.cash_after + row.stock_value
        cash, shares = row.cash_after, row.shares_after


# 비교 표에는 실제 부과한 비용과 가격에 반영한 슬리피지 환산액을 따로 남깁니다.
def summarize(frame, scenario, initial_cash):
    last = frame.iloc[-1]
    fees = sum(frame["commission"], ZERO)
    taxes = sum(frame["tax"], ZERO)
    slippage = sum(frame["slippage_amount"], ZERO)
    return {
        "scenario": scenario, "strategy": last["strategy"], "initial_cash": initial_cash,
        "final_cash": last["cash_after"], "final_shares": int(last["shares_after"]),
        "final_stock_value": last["stock_value"], "final_equity": last["equity"],
        "profit": last["equity"] - initial_cash,
        "return_pct": last["cumulative_return"] * 100,
        "mdd_pct": min(frame["drawdown"]) * 100,
        "buy_count": int(frame["action"].eq("매수").sum()),
        "sell_count": int(frame["action"].eq("매도").sum()),
        "total_commission": fees, "total_tax": taxes,
        "total_slippage": slippage, "total_cost": fees + taxes + slippage,
    }


# CSV를 저장하고 문자열로 재읽어 소수 금액을 포함한 모든 값이 보존됐는지 비교합니다.
def save_and_check(frame, path):
    frame.to_csv(path, index=False, encoding="utf-8")
    reread = pd.read_csv(path, dtype=str, keep_default_na=False)
    pd.testing.assert_frame_equal(reread, frame.astype(str), check_dtype=False)


def main():
    settings = load_settings()
    settings_text = (HERE / "cost_settings.json").read_text(encoding="utf-8")
    raw_settings = json.loads(settings_text)
    if any(Decimal(raw_settings[key]) != value for key, value in settings.items()):
        raise ValueError("설정파일이 계산 준비 중 변경되었습니다.")
    if raw_settings.get("tax_year") != 2025:
        raise ValueError("이번 실습은 2025년 매도 세금 설정을 사용합니다.")

    price_path = ROOT / "data/stock-day33/clean/005930_2025_clean.csv"
    signal_path = ROOT / "data/stock-day40/005930_2025_signals.csv"
    reference_path = ROOT / "data/stock-day41/005930_2025_comparison_daily.csv"
    prices = read_input(price_path, ["stock_code", "date", "open", "close"])
    signals = read_input(signal_path, [
        "stock_code", "date", "open", "close_signal", "previous_signal", "previous_date", "open_order",
    ])
    account_columns = [
        f"{prefix}_{name}" for prefix in ("cross", "hold") for name in (
            "action", "traded_shares", "cash", "shares", "equity", "cumulative_return",
            "running_peak", "drawdown",
        )
    ]
    reference = read_input(reference_path, ["stock_code", "date", "open", "close"] + account_columns)
    if len(prices) != 242 or prices["date"].iloc[0] != "2025-01-02" or prices["date"].iloc[-1] != "2025-12-30":
        raise ValueError("기존 실습의 2025년 242행 가격 데이터와 범위가 다릅니다.")
    for other in (signals, reference):
        if prices["date"].tolist() != other["date"].tolist():
            raise ValueError("입력 파일끼리 거래일이 다릅니다.")
        if list(map(read_price, prices["open"])) != list(map(read_price, other["open"])):
            raise ValueError("입력 파일끼리 시가가 다릅니다.")
    if list(map(read_price, prices["close"])) != list(map(read_price, reference["close"])):
        raise ValueError("원본과 41일차 종가가 다릅니다.")

    # 40일차 주문은 이미 다음 거래일로 배치돼 있습니다. 여기서는 다시 옮기지 않습니다.
    previous_dates = prices["date"].shift(1).fillna("")
    if signals["previous_date"].fillna("").tolist() != previous_dates.tolist():
        raise ValueError("전날 날짜와 다음 거래일 연결이 다릅니다.")
    if not signals["close_signal"].isin(["없음", "골든크로스", "데드크로스"]).all():
        raise ValueError("알 수 없는 마감 신호가 있습니다.")
    previous_signals = signals["close_signal"].shift(1).fillna("없음")
    if signals["previous_signal"].fillna("없음").tolist() != previous_signals.tolist():
        raise ValueError("전날 마감 신호 연결이 다릅니다.")
    actions = signals["open_order"].tolist()
    for action, signal in zip(actions, previous_signals):
        if action == "매수" and signal != "골든크로스":
            raise ValueError("매수 주문과 전날 골든크로스가 연결되지 않습니다.")
        if action == "매도" and signal != "데드크로스":
            raise ValueError("매도 주문과 전날 데드크로스가 연결되지 않습니다.")
    cross_dates = [date if action != "없음" else "" for date, action in zip(previous_dates, actions)]
    hold_actions = ["매수"] + ["없음"] * (len(prices) - 1)
    hold_dates = [""] * len(prices)

    # 비용이 모두 0이면 41일차 결과가 재현돼야 합니다.
    zero_settings = settings.copy()
    for key in ("buy_commission_rate", "sell_commission_rate", "sell_tax_rate", "slippage_rate"):
        zero_settings[key] = ZERO
    summaries, cost_frames = [], []
    for name, prefix, orders, dates in (
        ("교차 전략", "cross", actions, cross_dates),
        ("매수 후 보유", "hold", hold_actions, hold_dates),
    ):
        baseline = simulate(prices, orders, dates, zero_settings, name)
        check_baseline(baseline, reference, prefix)
        check_ledger(baseline, settings["initial_cash"])
        cost_frame = simulate(prices, orders, dates, settings, name)
        check_ledger(cost_frame, settings["initial_cash"])
        summaries.append(summarize(baseline, "비용 없음", settings["initial_cash"]))
        summaries.append(summarize(cost_frame, "비용 반영", settings["initial_cash"]))
        cost_frames.append(cost_frame)

    daily = pd.concat(cost_frames, ignore_index=True)
    fills = daily[daily["action"].isin(["매수", "매도"])].copy().reset_index(drop=True)
    summary = pd.DataFrame(summaries)
    output = ROOT / "data/stock-day44"
    output.mkdir(parents=True, exist_ok=True)
    save_and_check(daily, output / "005930_2025_cost_daily.csv")
    save_and_check(fills, output / "005930_2025_cost_fills.csv")
    save_and_check(summary, output / "005930_2025_cost_summary.csv")
    # 실제 계산에 사용한 요율과 설명을 결과 폴더에도 저장합니다.
    snapshot_path = output / "cost_settings_snapshot.json"
    snapshot_path.write_text(settings_text, encoding="utf-8")
    assert json.loads(snapshot_path.read_text(encoding="utf-8")) == raw_settings

    display = summary[["scenario", "strategy", "final_equity", "return_pct", "mdd_pct"]].copy()
    for column in ("final_equity", "return_pct", "mdd_pct"):
        places = 2 if column == "final_equity" else 4
        display[column] = display[column].map(lambda value: f"{value:,.{places}f}")
    display.columns = ["조건", "전략", "최종자산(원)", "수익률(%)", "최대낙폭(%)"]
    print(f"공통 초기자금: {settings['initial_cash']:,.0f}원")
    print(f"공통 기간: {prices['date'].iloc[0]} ~ {prices['date'].iloc[-1]} / {len(prices)}행")
    print("\n비용 전후 비교:")
    print(display.to_string(index=False))
    for row in summary[summary["scenario"].eq("비용 반영")].itertuples(index=False):
        print(f"\n[{row.strategy} 비용 반영]")
        print(f"최종 현금: {row.final_cash:,.2f}원 / 보유수량: {row.final_shares}주")
        print(f"수수료: {row.total_commission:,.0f}원 / 매도 세금: {row.total_tax:,.0f}원")
        print(f"슬리피지 환산액: {row.total_slippage:,.2f}원 / 세 항목 단순 합계: {row.total_cost:,.2f}원")
        print(f"모의 매수: {row.buy_count}회 / 모의 매도: {row.sell_count}회")
    print("\n비용0 조건에서 41일차 전체 거래일 대조: 통과")
    print("원본 가격·날짜·전날 신호 연결 검사: 통과")
    print("현금·수량 장부 연결·금액 검사: 통과")
    print("CSV 재읽기·설정 스냅샷 비교: 통과")
    print("슬리피지 환산액은 체결가격에 이미 포함됐으며 별도로 다시 차감하지 않습니다.")
    print("비용에 따른 수량 변화로 세 항목 합계와 최종 자산 감소액은 다를 수 있습니다.")
    print("마지막 보유 주식은 종가로 평가하며 강제 매도하지 않습니다.")
    print(f"저장 폴더: {output}")
    print("실제 API 요청·주문: 없음")


if __name__ == "__main__":
    main()
