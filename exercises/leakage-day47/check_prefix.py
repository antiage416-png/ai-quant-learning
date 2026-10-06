# 목적: 미래 자료 추가 전후의 과거 이동평균과 신호가 같은지 작은 예제로 검사합니다.
# 입력: 검증용 날짜·종가 35행입니다. 실제 삼성전자 시세가 아닙니다.
# 처리: 현재까지의 자료로 계산한 결과와 전체 계산의 같은 과거 구간을 비교합니다.
# 결과: 정상 계산 통과와 의도적으로 미래 신호를 사용한 계산의 탐지를 출력합니다.
# 40일차 파일·실제 CSV를 실행하거나 읽지 않으며 파일 저장·인터넷 요청은 없습니다.

import pandas as pd


# 날짜와 종가 표를 받아 과거부터 현재까지의 이동평균과 교차 신호를 반환합니다.
# 40일차의 교차·동률·초기 결측 조건을 그대로 옮긴 검증용 함수입니다.
# 이동평균은 저장된 지표를 가져오지 않고 전달받은 종가만으로 다시 계산합니다.
def calculate_signals(prices):
    if prices.empty or not {"date", "close"}.issubset(prices.columns):
        raise ValueError("날짜와 종가가 있는 비어 있지 않은 표가 필요합니다.")
    table = prices[["date", "close"]].copy().reset_index(drop=True)
    table["date"] = pd.to_datetime(table["date"], format="%Y-%m-%d", errors="raise")
    if table["date"].isna().any() or table["date"].duplicated().any():
        raise ValueError("날짜 결측 또는 중복이 있습니다.")
    if not table["date"].is_monotonic_increasing:
        raise ValueError("날짜가 시간순이 아닙니다.")
    table["close"] = pd.to_numeric(table["close"], errors="raise")
    if (table["close"].isna().any() or table["close"].le(0).any()
            or table["close"].isin([float("inf"), float("-inf")]).any()):
        raise ValueError("종가는 결측·무한대가 아닌 양수여야 합니다.")

    # center=False는 창의 오른쪽 끝을 현재 행에 두어 미래 행을 포함하지 않습니다.
    # min_periods는 창 길이만큼 과거 자료가 모여야 평균을 계산하도록 합니다.
    table["ma_5"] = table["close"].rolling(5, min_periods=5, center=False).mean()
    table["ma_20"] = table["close"].rolling(20, min_periods=20, center=False).mean()
    previous_5 = table["ma_5"].shift(1)
    previous_20 = table["ma_20"].shift(1)
    valid = (table["ma_5"].notna() & table["ma_20"].notna()
             & previous_5.notna() & previous_20.notna())
    golden = valid & (previous_5 <= previous_20) & (table["ma_5"] > table["ma_20"])
    dead = valid & (previous_5 >= previous_20) & (table["ma_5"] < table["ma_20"])
    table["close_signal"] = "없음"
    table.loc[golden, "close_signal"] = "골든크로스"
    table.loc[dead, "close_signal"] = "데드크로스"
    # 다음 거래일 시가 판단에 전달할 값도 전날 신호에서만 가져옵니다.
    table["previous_signal"] = table["close_signal"].shift(1, fill_value="없음")
    return table


# 일부러 잘못 만든 대조 함수입니다. 실제 신호 계산에 사용하면 안 됩니다.
# shift(-1)은 다음 행의 값을 오늘 행으로 끌어옵니다.
def calculate_with_future_signal(prices):
    table = calculate_signals(prices)
    table["close_signal"] = table["close_signal"].shift(-1, fill_value="없음")
    table["previous_signal"] = table["close_signal"].shift(1, fill_value="없음")
    return table


# calculator는 검사할 계산 함수, cut_points는 앞에서 몇 행까지 볼지 정한 목록입니다.
# 전체 계산을 자르기만 하지 않고, 매번 입력 자체를 잘라 처음부터 다시 계산합니다.
def find_changed_prefixes(prices, calculator, cut_points):
    full = calculator(prices.copy())
    changed = []
    for count in cut_points:
        if not isinstance(count, int) or not 1 <= count < len(prices):
            raise ValueError("비교 행 수는 1 이상 전체 행 수 미만이어야 합니다.")
        limited = calculator(prices.iloc[:count].copy()).reset_index(drop=True)
        expected = full.iloc[:count].reset_index(drop=True)
        try:
            # 초기 결측 위치도 비교하며 문자열 신호와 숫자 값을 모두 검사합니다.
            pd.testing.assert_frame_equal(limited, expected, check_exact=True)
        except AssertionError:
            changed.append(count)
    return changed


def main():
    # 같은 가격 20행 이후 상승·하락·재상승을 넣어 교차가 실제로 발생하도록 합니다.
    prices = pd.DataFrame({
        "date": pd.bdate_range("2025-03-04", periods=35).strftime("%Y-%m-%d"),
        "close": [100] * 20 + [120] * 5 + [80] * 5 + [130] * 5,
    })
    before = prices.copy(deep=True)
    full = calculate_signals(prices)
    # 단순히 신호가 전혀 없는 예제를 통과한 것은 아닌지 별도로 확인합니다.
    expected_signals = {20: "골든크로스", 27: "데드크로스", 32: "골든크로스"}
    actual_signals = full.loc[full["close_signal"].ne("없음"), "close_signal"].to_dict()
    assert actual_signals == expected_signals
    assert full["ma_5"].isna().sum() == 4
    assert full["ma_20"].isna().sum() == 19
    assert full["close_signal"].iloc[:20].eq("없음").all()
    assert full["previous_signal"].iloc[21] == "골든크로스"

    # range의 끝값 35는 제외되므로 앞 20행부터 앞 34행까지 총 15번 검사합니다.
    cut_points = list(range(20, len(prices)))
    normal_changes = find_changed_prefixes(prices, calculate_signals, cut_points)
    bad_changes = find_changed_prefixes(prices, calculate_with_future_signal, cut_points)
    assert normal_changes == []
    assert bad_changes and 20 in bad_changes
    pd.testing.assert_frame_equal(prices, before)

    print(f"예제 행 수: {len(prices)}행")
    print("정상 예제 교차: 골든크로스 2회 / 데드크로스 1회")
    print("초기 결측·동률 이후 교차·전날 신호 연결 검사: 통과")
    print(f"비교 지점: 앞 20행부터 34행까지 {len(cut_points)}개")
    print(f"정상 계산의 과거 결과 변화: {len(normal_changes)}개 지점")
    print("정상 계산의 과거 결과 불변 검사: 통과")
    print(f"의도적으로 미래 신호를 사용한 계산: {len(bad_changes)}개 지점에서 변화 탐지")

    # 앞 20행만 있을 때는 21번째 행의 교차를 알 수 없다는 차이를 보여줍니다.
    short_bad = calculate_with_future_signal(prices.iloc[:20])
    full_bad = calculate_with_future_signal(prices)
    date = full_bad["date"].iloc[19].strftime("%Y-%m-%d")
    print(f"잘못된 계산의 변경 예: {date}")
    print(f"  앞 20행만 입력: {short_bad['close_signal'].iloc[19]}")
    print(f"  전체 35행 입력: {full_bad['close_signal'].iloc[19]}")
    print("미래 신호 사용 탐지·입력 보존 검사: 통과")
    print("실제 CSV 조회·파일 저장·인터넷 요청: 없음")


if __name__ == "__main__":
    main()
