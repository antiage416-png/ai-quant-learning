# 목적: 휴장일과 거래일 데이터 누락을 작은 날짜 예제로 구분합니다.
# 입력: 34일차 기준의 2025년 6월 2일~5일 달력과 인위적으로 만든 날짜 목록입니다.
# 처리: 달력으로 다음 거래일을 찾고, 날짜 누락·중복·순서·범위 오류를 검사합니다.
# 결과: 정상 예제와 오류를 잡은 결과를 터미널에 출력합니다.
# 실제 종목 데이터는 읽지 않으며 파일 저장·인터넷 요청·실제 주문은 없습니다.

# pandas는 날짜 목록을 만들고 같은 형식으로 비교하는 데 사용합니다.
import pandas as pd


# 날짜 비교가 가능하도록 문자열 목록을 날짜 목록으로 변환합니다.
# 잘못된 날짜를 결측으로 바꿔 숨기지 않고 오류로 처리합니다.
def parse_dates(values):
    return pd.DatetimeIndex(
        pd.to_datetime(values, format="%Y-%m-%d", errors="raise")
    )


# 관측 날짜를 달력과 비교합니다. 이 예제는 전체 구간의 자료를 요구합니다.
# 누락을 거래정지로 단정하거나 다음 행의 날짜로 대신하지 않습니다.
def require_complete_dates(observed, calendar):
    if observed.hasnans or calendar.hasnans:
        raise ValueError("날짜에 결측값이 있습니다.")
    if calendar.has_duplicates or not calendar.is_monotonic_increasing:
        raise ValueError("기준 달력은 중복 없이 시간순이어야 합니다.")
    if observed.has_duplicates:
        raise ValueError("관측 날짜가 중복되었습니다.")
    if not observed.is_monotonic_increasing:
        raise ValueError("관측 날짜가 시간순이 아닙니다.")
    # difference는 왼쪽 목록에만 있는 날짜를 구합니다.
    missing = calendar.difference(observed).strftime("%Y-%m-%d").tolist()
    unexpected = observed.difference(calendar).strftime("%Y-%m-%d").tolist()
    if missing or unexpected:
        raise ValueError(f"누락 거래일: {missing} / 기준 밖 날짜: {unexpected}")


# 신호일 다음의 거래일을 기준 달력에서 찾습니다.
# 달력의 마지막 날이면 다음 거래일을 확인할 수 없으므로 None을 반환합니다.
def next_trading_day(signal_date, calendar):
    require_complete_dates(calendar, calendar)
    signal_date = pd.to_datetime(signal_date, format="%Y-%m-%d", errors="raise")
    if signal_date not in calendar:
        raise ValueError("신호일이 기준 거래일에 없습니다.")
    later = calendar[calendar > signal_date]
    return later[0] if len(later) else None


def main():
    # 이 짧은 예제 구간에는 34일차 기준 휴장일인 6월 3일만 들어 있습니다.
    # bdate_range는 주말만 제외하므로 휴장일은 별도로 제외합니다.
    weekdays = pd.bdate_range("2025-06-02", "2025-06-05")
    holidays = parse_dates(["2025-06-03"])
    calendar = weekdays[~weekdays.isin(holidays)]
    normal_dates = parse_dates(["2025-06-02", "2025-06-04", "2025-06-05"])
    require_complete_dates(normal_dates, calendar)
    planned_date = next_trading_day("2025-06-02", calendar)
    assert planned_date == pd.Timestamp("2025-06-04")
    assert next_trading_day("2025-06-05", calendar) is None

    print("작은 예제의 기준 거래일:", calendar.strftime("%Y-%m-%d").tolist())
    print("정상 날짜 목록 검사: 통과")
    print("6월 2일 신호의 다음 거래일:", planned_date.strftime("%Y-%m-%d"))

    # 같은 달력에 대해 6월 4일 행이 빠진 자료를 인위적으로 만듭니다.
    # 다음 관측 행은 5일이지만 주문 예정일인 4일을 바꾸지는 않습니다.
    missing_dates = parse_dates(["2025-06-02", "2025-06-05"])
    following_row = missing_dates[missing_dates > pd.Timestamp("2025-06-02")][0]
    assert following_row == pd.Timestamp("2025-06-05")
    assert following_row != planned_date
    print("누락 예제의 다음 관측 행:", following_row.strftime("%Y-%m-%d"))

    # try에서 검사하고, except에서 예상한 오류를 잡아 예제 검증을 계속합니다.
    # 실제 계산에서는 이 오류를 무시한 채 매매 계산을 계속하면 안 됩니다.
    try:
        require_complete_dates(missing_dates, calendar)
    except ValueError as error:
        assert "2025-06-04" in str(error)
        print("누락 예제에서 예상한 오류:", error)
    else:
        raise AssertionError("누락 거래일을 잡지 못했습니다.")

    # 중복·역순·휴장일 포함도 정상 자료로 통과시키지 않는지 확인합니다.
    invalid_cases = [
        ("중복 날짜", parse_dates(["2025-06-02", "2025-06-04", "2025-06-04", "2025-06-05"])),
        ("날짜 역순", normal_dates[::-1]),
        ("휴장일 포함", weekdays),
    ]
    for name, dates in invalid_cases:
        try:
            require_complete_dates(dates, calendar)
        except ValueError:
            print(f"{name} 차단 검사: 통과")
        else:
            raise AssertionError(f"잘못된 자료를 통과시켰습니다: {name}")

    print("마지막 거래일의 다음 날짜 미확인 처리: 통과")
    print("휴장일과 데이터 누락 구분 검사: 통과")
    print("실제 API 요청·주문·파일 저장: 없음")


# 직접 실행할 때만 예제를 돌립니다. 다른 코드에서 가져오면 함수만 사용합니다.
if __name__ == "__main__":
    main()
