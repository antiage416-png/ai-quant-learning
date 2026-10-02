# 목적: 관측 비율·평균·분산·표준편차·상관관계를 복습합니다.
# 입력: 설명용 수익률 +10%, -10%, +5%, -5%
# 처리: 통계 계산 → 손계산과 비교 → 의미 확인
# 출력: 계산 결과와 검증 결과
# 실제 데이터 조회·API 요청·파일 저장은 없습니다.

from math import isclose

import pandas as pd


# 수익률은 소수 단위로 저장합니다. 0.10은 10%입니다.
returns = pd.Series([0.10, -0.10, 0.05, -0.05])

# gt(0)은 각 값이 0보다 큰지 확인합니다.
# 참인 값의 수를 전체 관측 수로 나눕니다.
positive_count = int(returns.gt(0).sum())
positive_rate = positive_count / len(returns)

# mean은 산술평균입니다. 누적수익률과는 다릅니다.
mean_return = returns.mean()

# ddof=0은 이 네 값 전체의 제곱 편차 합을 4로 나눕니다.
# ddof=1은 표본분산으로, 제곱 편차 합을 3으로 나눕니다.
variance_all = returns.var(ddof=0)
variance_sample = returns.var(ddof=1)
std_sample = returns.std(ddof=1)

# 누적수익률은 가격 배수를 곱한 뒤 1을 빼서 구합니다.
cumulative_return = (1 + returns).prod() - 1

# 관계를 설명하기 위한 인위적인 비교 자료입니다.
twice_returns = returns * 2
opposite_returns = returns * -2

# corr는 기본적으로 피어슨 상관계수를 계산합니다.
# 선형 관계의 방향과 강도를 나타냅니다.
same_direction_corr = returns.corr(twice_returns)
opposite_direction_corr = returns.corr(opposite_returns)

# 손계산:
# 평균은 0이고, 제곱 편차 합은
# 0.10² + (-0.10)² + 0.05² + (-0.05)² = 0.025입니다.
expected = {
    "양수 비율": (positive_rate, 0.5),
    "평균": (mean_return, 0.0),
    "전체 값 기준 분산": (variance_all, 0.025 / 4),
    "표본분산": (variance_sample, 0.025 / 3),
    "표본표준편차": (std_sample, (0.025 / 3) ** 0.5),
    "누적수익률": (cumulative_return, -0.012475),
    "같은 방향 상관계수": (same_direction_corr, 1.0),
    "반대 방향 상관계수": (opposite_direction_corr, -1.0),
}

for name, (actual, hand_calculated) in expected.items():
    if not isclose(actual, hand_calculated, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError(f"{name}이 손계산 결과와 다릅니다.")

print(f"관측 수: {len(returns)}개")
print(f"양수 수익률: {positive_count}개")
print(f"양수 수익률의 관측 비율: {positive_rate:.2%}")
print(f"산술평균 수익률: {mean_return:.4%}")
print(f"전체 값 기준 분산: {variance_all:.8f}")
print(f"표본분산: {variance_sample:.8f}")
print(f"표본표준편차: {std_sample:.4%}")
print(f"누적수익률: {cumulative_return:.4%}")
print(f"두 배 수익률과의 상관계수: {same_direction_corr:.4f}")
print(f"음의 두 배 수익률과의 상관계수: {opposite_direction_corr:.4f}")
print("\n통계 손계산 비교: 통과")