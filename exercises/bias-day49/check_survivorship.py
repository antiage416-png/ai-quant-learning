# 목적: 가상 세 종목에 동일한 초기 금액을 투자한 결과를 확인합니다.
# 입력 → 처리 → 결과: 종목별 초기·종료 금액 → 합계 → 포트폴리오 수익률.
# 같은 기간이며 추가 매매·입출금은 없고 비용·배당은 제외합니다.
# 파일 저장·인터넷 요청·실제 주문은 없습니다.

# 리스트의 순서는 가, 나, 다입니다. 각 위치는 같은 종목을 나타냅니다.
initial_values = [1_000_000, 1_000_000, 1_000_000]
ending_values = [1_200_000, 1_100_000, 100_000]

# sum()은 리스트 안의 금액을 모두 더합니다.
total_initial = sum(initial_values)
total_ending = sum(ending_values)

# 추가 입출금이 없으므로 전체 종료 자산을 전체 초기 자금과 비교합니다.
portfolio_return = total_ending / total_initial - 1

print(f"전체 초기 자금: {total_initial:,}원")
print(f"전체 종료 자산: {total_ending:,}원")

# :.2%는 소수 수익률을 100배 한 퍼센트로 소수점 두 자리까지 표시합니다.
print(f"전체 포트폴리오 기간 수익률: {portfolio_return:.2%}")

# 종료 시점에 살아남은 가·나만 사후에 선택한 비교입니다.
# [:2]는 리스트에서 처음 두 항목을 가져옵니다. 원래 리스트는 그대로입니다.
survivor_initial = sum(initial_values[:2])
survivor_ending = sum(ending_values[:2])

# 선택한 두 종목의 초기 자금 대비 종료 자산으로 기간 수익률을 계산합니다.
survivor_return = survivor_ending / survivor_initial - 1

# 두 수익률의 차이는 퍼센트포인트로 표시합니다.
gap_percentage_points = (survivor_return - portfolio_return) * 100

print(f"생존 종목만의 초기 자금: {survivor_initial:,}원")
print(f"생존 종목만의 종료 자산: {survivor_ending:,}원")
print(f"생존 종목만의 기간 수익률: {survivor_return:.2%}")
print(f"전체 대비 수익률 차이: {gap_percentage_points:.2f}%p")

# isclose는 소수 계산에서 생기는 작은 표현 오차를 허용해 비교합니다.
from math import isclose

# 금액은 정수이므로 정확히 비교합니다.
assert total_initial == 3_000_000
assert total_ending == 2_400_000
assert survivor_initial == 2_000_000
assert survivor_ending == 2_300_000

# rel_tol=0은 상대 오차를 사용하지 않는다는 뜻입니다.
# abs_tol=1e-12는 절대 차이가 0.000000000001 이하면 같다고 판단합니다.
assert isclose(portfolio_return, -0.20, rel_tol=0, abs_tol=1e-12)
assert isclose(survivor_return, 0.15, rel_tol=0, abs_tol=1e-12)
assert isclose(gap_percentage_points, 35.0, rel_tol=0, abs_tol=1e-12)

print("초기·종료 금액과 기간 수익률 손계산 비교: 통과")