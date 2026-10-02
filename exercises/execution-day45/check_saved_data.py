# 목적: 저장된 종목별 날짜와 기존 주문 예정일을 34일차 거래일 기준과 대조합니다.
# 입력: 34일차 휴장일 정의, 33일차 정리 CSV 5개, 40일차 삼성전자 신호 CSV입니다.
# 처리: 날짜 누락·중복·순서, 시가·종가 유효성, 다음 거래일 주문 연결을 검사합니다.
# 결과: 파일별 검사 결과와 날짜가 연결된 주문 수를 터미널에 출력합니다.
# 원본·기존 결과·보고서를 변경하지 않습니다. 결과 저장·인터넷 요청·실제 주문은 없습니다.

# ast는 Python 코드를 실행하지 않고 구조를 읽는 표준 모듈입니다.
import ast
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd

# 같은 폴더에서 이미 검증한 날짜 비교와 다음 거래일 함수를 가져옵니다.
from check_calendar_rules import next_trading_day, parse_dates, require_complete_dates


ROOT = Path(__file__).resolve().parents[2]
STOCK_CODES = ["005930", "000660", "005380", "035420", "055550"]


# 34일차 파일에서 HOLIDAYS에 직접 적은 사전만 읽어 반환합니다.
# 파일 전체를 실행하면 보고서를 다시 저장하므로 실행이나 일반 import를 하지 않습니다.
# literal_eval은 문자열·숫자·사전 같은 자료만 해석하며 함수 호출을 실행하지 않습니다.
def read_holidays(path):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    matches = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "HOLIDAYS" for target in node.targets):
                matches.append(node.value)
    if len(matches) != 1:
        raise ValueError("34일차 휴장일 정의가 하나가 아닙니다. 원본 코드를 확인해야 합니다.")
    holidays = ast.literal_eval(matches[0])
    if not isinstance(holidays, dict) or not holidays:
        raise ValueError("34일차 휴장일 정의가 비어 있거나 사전 형식이 아닙니다.")
    if not all(isinstance(date, str) and isinstance(reason, str) for date, reason in holidays.items()):
        raise ValueError("휴장일과 사유는 문자열이어야 합니다.")
    return holidays


# 기존 34일차와 같은 방식으로 2025년 평일에서 휴장일을 제외합니다.
# 이 기준은 직접 내려받은 KRX 달력 파일이 아닌, 당시 구성한 비교 기준입니다.
def build_calendar():
    path = ROOT / "exercises" / "quality-day34" / "check_calendar.py"
    holidays = parse_dates(list(read_holidays(path)))
    weekdays = pd.bdate_range("2025-01-01", "2025-12-31")
    if holidays.hasnans or holidays.has_duplicates or not holidays.isin(weekdays).all():
        raise ValueError("기존 휴장일 목록에 2025년 평일이 아닌 날짜 또는 중복이 있습니다.")
    calendar = weekdays[~weekdays.isin(holidays)]
    if len(calendar) != 242:
        raise ValueError("기존 2025년 242거래일 기준과 다릅니다. 달력을 먼저 확인해야 합니다.")
    return calendar


# 앞자리 0과 빈 문자열을 보존하면서 CSV를 읽고 필수 열과 종목을 확인합니다.
def read_csv(path, required, code):
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f"필수 열 누락: {path.name}, {sorted(missing)}")
    if frame.empty or not frame["stock_code"].eq(code).all():
        raise ValueError(f"빈 자료 또는 종목코드 불일치: {path.name}")
    return frame


# 시가·종가 오류를 거래정지로 분류하거나 이전 가격으로 덮지 않습니다.
def positive_prices(values, label):
    try:
        prices = [Decimal(value) for value in values]
    except InvalidOperation as error:
        raise ValueError(f"숫자로 읽을 수 없는 가격: {label}") from error
    if any(not price.is_finite() or price <= 0 for price in prices):
        raise ValueError(f"가격 결측·0·음수·무한대: {label}")
    return prices


def main():
    calendar = build_calendar()
    print("비교 기준: 34일차 휴장일 목록을 그대로 읽어 구성한 2025년 달력")
    print(f"기준 거래일 수: {len(calendar)}개")
    prices_by_code = {}
    for code in STOCK_CODES:
        path = ROOT / "data" / "stock-day33" / "clean" / f"{code}_2025_clean.csv"
        frame = read_csv(path, ["stock_code", "date", "open", "close"], code)
        require_complete_dates(parse_dates(frame["date"]), calendar)
        positive_prices(frame["open"], f"{code} 시가")
        positive_prices(frame["close"], f"{code} 종가")
        prices_by_code[code] = frame
        print(f"{code}: {len(frame)}행 / 날짜·시가·종가 검사: 통과")

    signal_path = ROOT / "data" / "stock-day40" / "005930_2025_signals.csv"
    signals = read_csv(signal_path, [
        "stock_code", "date", "open", "close_signal", "previous_signal", "previous_date", "open_order",
    ], "005930")
    require_complete_dates(parse_dates(signals["date"]), calendar)
    prices = prices_by_code["005930"]
    if positive_prices(signals["open"], "40일차 시가") != positive_prices(prices["open"], "33일차 시가"):
        raise ValueError("33일차와 40일차의 시가가 다릅니다.")

    # 전날 날짜와 전날 마감 신호가 같은 행의 주문에 연결되었는지 검사합니다.
    # shift는 대조용 기대값에만 사용합니다. 기존 주문 행은 이동하지 않습니다.
    if signals["previous_date"].tolist() != signals["date"].shift(1).fillna("").tolist():
        raise ValueError("전날 날짜 연결이 다릅니다.")
    if not signals["close_signal"].isin(["없음", "골든크로스", "데드크로스"]).all():
        raise ValueError("확인할 수 없는 마감 신호가 있습니다.")
    previous = signals["close_signal"].shift(1).fillna("없음").tolist()
    actual_previous = [value or "없음" for value in signals["previous_signal"]]
    if actual_previous != previous:
        raise ValueError("전날 마감 신호 연결이 다릅니다.")

    planned_count = 0
    for row in signals.itertuples(index=False):
        if row.open_order not in {"없음", "매수", "매도"}:
            raise ValueError(f"확인할 수 없는 주문 행동: {row.date}")
        if row.open_order == "없음":
            continue
        needed_signal = "골든크로스" if row.open_order == "매수" else "데드크로스"
        if row.previous_signal != needed_signal:
            raise ValueError(f"주문 행동과 전날 신호 불일치: {row.date}")
        expected = next_trading_day(row.previous_date, calendar)
        if expected != pd.Timestamp(row.date):
            raise ValueError(f"기준 달력의 다음 거래일과 주문 예정일 불일치: {row.date}")
        planned_count += 1

    print(f"\n40일차 주문 예정일·전날 신호 연결: {planned_count}건 통과")
    print("기존 주문 날짜 다시 이동: 없음")
    print("이 검사는 실제 거래정지 여부나 실제 체결 가능성을 입증하지 않습니다.")
    print("일봉 시가가 있어도 주문 전량 체결은 기존 실습 가정입니다.")
    print("과거 거래정지·체결 불가를 적용하려면 해당 시점의 별도 근거가 필요합니다.")
    print("실제 API 요청·주문·결과 파일 저장: 없음")


if __name__ == "__main__":
    main()
