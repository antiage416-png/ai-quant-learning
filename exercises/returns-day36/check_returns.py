# 목적: 단순수익률과 누적수익률을 손계산 결과와 비교합니다.
# 입력: 예제 가격 100 → 110 → 99
# 처리: 직전 가격 대비 변화율과 처음 대비 누적 변화율을 계산합니다.
# 출력: 계산 표와 손계산 비교 결과
# 파일 저장이나 API 요청은 없습니다.

import pandas as pd
from math import isclose


# Series는 순서가 있는 한 열의 데이터입니다.
prices = pd.Series([100.0, 110.0, 99.0], name="price")

# pct_change는 직전 값 대비 변화율을 계산합니다.
# 반환값 0.1은 10%를 뜻합니다.
# fill_method=None으로 누락된 가격을 자동으로 채우지 않습니다.
daily_return = prices.pct_change(fill_method=None)

# 첫 가격을 기준으로 각 시점의 누적수익률을 직접 계산합니다.
cumulative_direct = prices / prices.iloc[0] - 1

# 수익률에 1을 더하면 가격 배수가 됩니다.
# 예: +10% → 1.1배, -10% → 0.9배
growth_factor = 1 + daily_return

# 첫날은 직전 가격이 없어 수익률이 NaN입니다.
# 곱셈의 출발점으로 첫날의 배수만 1로 정합니다.
# 다른 위치의 결측값까지 일괄적으로 채우지는 않습니다.
growth_factor.iloc[0] = 1.0

# cumprod는 앞에서부터 값을 누적해서 곱합니다.
# 누적 가격 배수에서 1을 빼면 누적수익률이 됩니다.
cumulative_compound = growth_factor.cumprod() - 1

# 출력할 때만 100을 곱해 퍼센트 단위로 표시합니다.
result = pd.DataFrame({
    "가격": prices,
    "단순수익률(%)": daily_return * 100,
    "누적수익률_직접(%)": cumulative_direct * 100,
    "누적수익률_곱셈(%)": cumulative_compound * 100,
})
result.index = ["첫날", "둘째 날", "셋째 날"]

print(result.to_string(float_format=lambda value: f"{value:.2f}"))

# 소수 계산에는 작은 오차가 생길 수 있어 isclose로 비교합니다.
# abs_tol은 0 근처의 값도 비교할 수 있도록 허용하는 절대 오차입니다.
expected_daily = [0.10, -0.10]
for actual, expected in zip(daily_return.iloc[1:], expected_daily):
    if not isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError("단순수익률이 손계산과 다릅니다.")

# 첫날의 단순수익률은 계산할 수 없다는 점도 확인합니다.
if not pd.isna(daily_return.iloc[0]):
    raise ValueError("첫날 단순수익률은 결측값이어야 합니다.")

# 두 누적수익률 계산법을 모든 시점에서 비교합니다.
for direct, compound in zip(cumulative_direct, cumulative_compound):
    if not isclose(direct, compound, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError("누적수익률 계산법 사이에 차이가 있습니다.")

if not isclose(
    cumulative_compound.iloc[-1], -0.01,
    rel_tol=1e-9, abs_tol=1e-12
):
    raise ValueError("최종 누적수익률이 손계산 -1%와 다릅니다.")

print("\n단순수익률 손계산 비교: 통과")
print("누적수익률 두 계산법 비교: 통과")
print("최종 누적수익률 손계산 비교: 통과")

# 단순 합산과 실제 누적 계산이 다르다는 것을 표시합니다.
print(f"\n단순수익률의 합: {daily_return.sum():.2%}")
print(f"실제 누적수익률: {cumulative_compound.iloc[-1]:.2%}")

