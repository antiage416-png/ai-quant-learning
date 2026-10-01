# 목적: 자산가치·누적수익률·낙폭·최대낙폭을 손계산과 비교합니다.
# 입력: 예제 자산가치 100 → 120 → 90 → 108 → 130
# 처리: 누적 최고값과 낙폭을 계산하고 기대 결과와 비교합니다.
# 출력: 계산 표와 검증 결과
# 파일 저장이나 API 요청은 없습니다.

from math import isclose

import pandas as pd


# 외부 입출금이 없는 하나의 자산가치 경로를 가정합니다.
equity = pd.Series(
    [100.0, 120.0, 90.0, 108.0, 130.0],
    name="equity",
)

# 처음 자산가치 대비 누적수익률을 계산합니다.
cumulative_return = equity / equity.iloc[0] - 1

# cummax는 각 시점까지 등장한 값 중 가장 큰 값을 구합니다.
# 미래의 최고값을 미리 사용하는 것이 아닙니다.
running_peak = equity.cummax()

# 현재 자산가치를 그때까지 최고값과 비교합니다.
# 새 고점에서는 0, 고점보다 내려오면 음수가 됩니다.
drawdown = equity / running_peak - 1

# 음수로 표시한 낙폭 중 가장 작은 값이 최대낙폭입니다.
max_drawdown = drawdown.min()

# 손으로 계산한 누적 최고값과 낙폭입니다.
expected_peaks = [100.0, 120.0, 120.0, 120.0, 130.0]
expected_drawdowns = [0.0, 0.0, -0.25, -0.10, 0.0]

for actual, expected in zip(running_peak, expected_peaks):
    if not isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError("누적 최고값이 손계산과 다릅니다.")

for actual, expected in zip(drawdown, expected_drawdowns):
    if not isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError("낙폭이 손계산과 다릅니다.")

if not isclose(max_drawdown, -0.25, rel_tol=1e-9, abs_tol=1e-12):
    raise ValueError("최대낙폭이 손계산 -25%와 다릅니다.")

# 수익률은 계산 중 소수 단위로 유지하고, 출력할 때만 100을 곱합니다.
result = pd.DataFrame({
    "자산가치": equity,
    "누적수익률(%)": cumulative_return * 100,
    "누적최고값": running_peak,
    "낙폭(%)": drawdown * 100,
})
result.index = range(1, len(result) + 1)
result.index.name = "순서"

print(result.to_string(float_format=lambda value: f"{value:.2f}"))
print(f"\n최종 누적수익률: {cumulative_return.iloc[-1]:.2%}")
print(f"최대낙폭(MDD): {max_drawdown:.2%}")
print("누적 최고값 손계산 비교: 통과")
print("낙폭 손계산 비교: 통과")
print("최대낙폭 손계산 비교: 통과")