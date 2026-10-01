# 목적: 이동평균의 계산 구간과 초기 결측값을 확인합니다.
# 입력: 예제 가격 100 → 110 → 90 → 120 → 150
# 처리: 최근 3개 가격의 평균을 계산하고 손계산과 비교합니다.
# 출력: 계산 표와 검증 결과
# 파일 저장이나 API 요청은 없습니다.

from math import isclose

import pandas as pd


prices = pd.Series(
    [100.0, 110.0, 90.0, 120.0, 150.0],
    name="price",
)

# window=3은 현재 행을 포함해 최근 3개 행을 묶는다는 뜻입니다.
# min_periods=3은 유효한 값 3개가 모여야 계산하도록 합니다.
# mean()은 각 구간의 산술평균을 구합니다.
moving_average = prices.rolling(
    window=3,
    min_periods=3,
).mean()

# 첫 두 행은 자료가 부족하므로 결측값이어야 합니다.
if not moving_average.iloc[:2].isna().all():
    raise ValueError("첫 두 행은 결측값이어야 합니다.")

# 세 번째 행부터는 손으로 계산한 평균과 비교합니다.
expected = [
    (100 + 110 + 90) / 3,
    (110 + 90 + 120) / 3,
    (90 + 120 + 150) / 3,
]

for actual, hand_calculated in zip(moving_average.iloc[2:], expected):
    # 소수 계산의 작은 오차를 허용하며 비교합니다.
    if not isclose(actual, hand_calculated, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError("이동평균이 손계산 결과와 다릅니다.")

result = pd.DataFrame({
    "가격": prices,
    "3개_이동평균": moving_average,
})

# 화면의 행 번호만 1부터 표시합니다.
result.index = range(1, len(result) + 1)
result.index.name = "순서"

print(result.to_string(float_format=lambda value: f"{value:.2f}"))
print(f"\n이동평균 결측값 수: {moving_average.isna().sum()}")
print(f"계산된 이동평균 수: {moving_average.count()}")
print("초기 결측 구간 확인: 통과")
print("이동평균 손계산 비교: 통과")