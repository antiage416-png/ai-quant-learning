# 목적: 합의한 날짜 경계로 개발·검증·최종 평가 구간을 나누는 방법을 검증합니다.
# 입력: 구간 경계에 놓인 가상 날짜 6개와 행을 구별하는 일련번호입니다.
# 처리: 시간순으로 분리하고 날짜 중복·누락·범위 오류와 원본 복원을 검사합니다.
# 결과: 구간별 날짜와 검사 결과를 터미널에 출력합니다.
# 실제 가격 데이터 조회·파일 저장·인터넷 요청은 없습니다.

import pandas as pd


# 사용자가 선택한 세 구간입니다. 자료가 있는 첫날과 마지막 날을 경계로 적었습니다.
# 개발·검증·최종 평가의 순서이며 수익률을 보고 경계를 바꾸지 않습니다.
PERIODS = {
    "development": {"label": "개발", "start": "2025-01-02", "end": "2025-06-30"},
    "validation": {"label": "검증", "start": "2025-07-01", "end": "2025-09-30"},
    "final_evaluation": {"label": "최종 평가", "start": "2025-10-01", "end": "2025-12-30"},
}


# date 열을 가진 표를 받아 세 구간의 표를 사전으로 반환합니다.
# 기존 순서를 먼저 검사하므로 잘못된 순서를 몰래 정렬해 숨기지 않습니다.
def split_by_period(frame):
    if frame.empty or "date" not in frame.columns:
        raise ValueError("날짜 열이 있는 비어 있지 않은 표가 필요합니다.")
    dates = pd.to_datetime(frame["date"], format="%Y-%m-%d", errors="raise")
    if dates.isna().any() or dates.duplicated().any():
        raise ValueError("날짜에 결측 또는 중복이 있습니다.")
    if not dates.is_monotonic_increasing:
        raise ValueError("날짜가 시간순이 아닙니다.")

    # between은 시작일과 종료일을 모두 포함하는지 검사합니다.
    # 각 열은 해당 구간에 들어가는 행이면 True, 아니면 False입니다.
    membership = pd.DataFrame({
        key: dates.between(period["start"], period["end"], inclusive="both")
        for key, period in PERIODS.items()
    })
    # True를 1로 합산하면 각 행이 몇 구간에 속하는지 알 수 있습니다.
    # 0이면 범위 밖 또는 구간 사이 누락이고, 2 이상이면 중복 배정입니다.
    if not membership.sum(axis=1).eq(1).all():
        raise ValueError("각 행은 정확히 한 구간에 속해야 합니다. 경계와 날짜 범위를 확인하세요.")
    parts = {key: frame.loc[membership[key]].copy() for key in PERIODS}
    if any(part.empty for part in parts.values()):
        raise ValueError("비어 있는 구간이 있습니다. 이번 실습은 세 구간의 자료를 모두 요구합니다.")

    # concat으로 시간순 재결합한 표가 입력 표와 같은지 모든 열을 비교합니다.
    restored = pd.concat(parts.values(), ignore_index=True)
    pd.testing.assert_frame_equal(restored, frame.reset_index(drop=True))
    return parts


def main():
    # 일련번호는 행이 사라지거나 복제되지 않았는지 확인하기 위한 값이며 가격이 아닙니다.
    sample = pd.DataFrame({
        "date": [
            "2025-01-02", "2025-06-30", "2025-07-01",
            "2025-09-30", "2025-10-01", "2025-12-30",
        ],
        "row_id": [1, 2, 3, 4, 5, 6],
    })
    before = sample.copy(deep=True)
    parts = split_by_period(sample)
    expected_ids = {"development": [1, 2], "validation": [3, 4], "final_evaluation": [5, 6]}
    for key, part in parts.items():
        assert part["row_id"].tolist() == expected_ids[key]
        print(f"{PERIODS[key]['label']}: {len(part)}행 / {part['date'].tolist()}")
    pd.testing.assert_frame_equal(sample, before)
    print("경계 날짜 배정·중복 없는 분리 검사: 통과")
    print("재결합 원본 복원·입력 보존 검사: 통과")

    # 잘못된 입력을 인위적으로 만들어 조용히 제외하거나 정렬하지 않는지 확인합니다.
    invalid_cases = {
        "날짜 역순": sample.iloc[::-1].reset_index(drop=True),
        "중복 날짜": pd.concat([sample.iloc[:1], sample], ignore_index=True),
        "범위 밖 날짜": pd.concat([
            sample, pd.DataFrame({"date": ["2026-01-02"], "row_id": [7]})
        ], ignore_index=True),
        "날짜 결측": sample.assign(date=sample["date"].mask(sample.index == 0, "")),
    }
    for label, invalid in invalid_cases.items():
        try:
            split_by_period(invalid)
        except ValueError:
            print(f"{label} 차단 검사: 통과")
        else:
            raise AssertionError(f"잘못된 자료를 통과시켰습니다: {label}")
    print("실제 데이터 조회·파일 저장·인터넷 요청: 없음")


# 직접 실행할 때만 작은 예제를 돌리고, 다음 실습에서는 분리 함수만 가져옵니다.
if __name__ == "__main__":
    main()
