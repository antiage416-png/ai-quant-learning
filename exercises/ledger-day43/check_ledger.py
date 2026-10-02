# 목적: 주문·모의 체결·현금·보유수량을 서로 연결해 기록합니다.
# 입력: 초기자금 1,000만원과 검증용 주문·모의 체결 2건
# 처리: 체결 기록을 근거로 현금과 보유수량 장부를 작성합니다.
# 출력: 네 기록과 손계산 비교 결과
# 실제 주문·API 요청·파일 저장은 없습니다.
# 비용·배당·현금 이자는 제외합니다.

import pandas as pd


INITIAL_CASH = 10_000_000

# 주문은 행동 의도입니다. 아직 계좌 잔액을 변경하지 않습니다.
orders = pd.DataFrame({
    "주문ID": ["O001", "O002"],
    "신호확인일": pd.to_datetime(["2025-02-11", "2025-02-13"]),
    "주문예정일": pd.to_datetime(["2025-02-12", "2025-02-14"]),
    "행동": ["매수", "매도"],
    "수량규칙": ["가용 현금 내 최대 정수 수량", "보유 전량"],
})

# 이전 손계산 예제의 결과로 모의 체결 2건을 만듭니다.
# 181주는 매수일 시가 55,100원에서 계산한 수량입니다.
# 신호확인일에 다음 날 가격을 미리 알았다는 뜻은 아닙니다.
fills = pd.DataFrame({
    "체결ID": ["F001", "F002"],
    "주문ID": ["O001", "O002"],
    "모의체결일": pd.to_datetime(["2025-02-12", "2025-02-14"]),
    "행동": ["매수", "매도"],
    "체결수량": [181, 181],
    "가정가격": [55_100, 53_300],
})
fills["체결금액"] = fills["체결수량"] * fills["가정가격"]

# ID는 각 기록을 구분하고 서로 연결하는 이름입니다.
if orders["주문ID"].duplicated().any() or fills["체결ID"].duplicated().any():
    raise ValueError("중복 ID가 있습니다.")

if not orders["신호확인일"].lt(orders["주문예정일"]).all():
    raise ValueError("주문예정일은 신호확인일 이후여야 합니다.")

# 이번 예제는 주문마다 한 번씩 전량 체결된 경우입니다.
# 일반적인 부분 체결까지 구현한 것은 아닙니다.
if set(fills["주문ID"]) != set(orders["주문ID"]):
    raise ValueError("주문과 체결의 연결을 확인해야 합니다.")

linked = fills.merge(
    orders,
    on="주문ID",
    validate="one_to_one",
    suffixes=("_체결", "_주문"),
)

if (
    not linked["행동_체결"].eq(linked["행동_주문"]).all()
    or not linked["모의체결일"].eq(linked["주문예정일"]).all()
):
    raise ValueError("주문과 체결의 행동 또는 날짜가 다릅니다.")

cash = INITIAL_CASH
shares = 0
cash_records = []
position_records = []

for date in pd.to_datetime(["2025-02-12", "2025-02-13", "2025-02-14"]):
    cash_before = cash
    shares_before = shares

    # 오늘 체결된 기록만 계좌에 반영합니다.
    today_fills = fills.loc[fills["모의체결일"].eq(date)]

    for _, fill in today_fills.iterrows():
        quantity = int(fill["체결수량"])
        price = int(fill["가정가격"])
        amount = int(fill["체결금액"])

        if quantity <= 0 or price <= 0:
            raise ValueError("체결 수량과 가격은 양수여야 합니다.")

        if fill["행동"] == "매수":
            if shares != 0 or quantity != cash // price:
                raise ValueError("최대 정수 수량 매수 규칙과 다릅니다.")
            cash -= amount
            shares += quantity

        elif fill["행동"] == "매도":
            if shares == 0 or quantity != shares:
                raise ValueError("보유 전량 매도 규칙과 다릅니다.")
            cash += amount
            shares -= quantity

        else:
            raise ValueError("정의되지 않은 체결 행동입니다.")

    cash_records.append({
        "날짜": date,
        "시작현금": cash_before,
        "현금변화": cash - cash_before,
        "마감현금": cash,
    })
    position_records.append({
        "날짜": date,
        "시작수량": shares_before,
        "수량변화": shares - shares_before,
        "마감수량": shares,
    })

cash_book = pd.DataFrame(cash_records)
position_book = pd.DataFrame(position_records)

# 손계산한 현금·수량 변화와 정확히 비교합니다.
if cash_book["현금변화"].tolist() != [-9_973_100, 0, 9_647_300]:
    raise ValueError("현금 변화가 손계산과 다릅니다.")

if cash_book["마감현금"].tolist() != [26_900, 26_900, 9_674_200]:
    raise ValueError("현금 잔액이 손계산과 다릅니다.")

if position_book["수량변화"].tolist() != [181, 0, -181]:
    raise ValueError("수량 변화가 손계산과 다릅니다.")

if position_book["마감수량"].tolist() != [181, 181, 0]:
    raise ValueError("보유 수량이 손계산과 다릅니다.")

# 전날 마감 상태가 다음 날 시작 상태로 이어지는지 확인합니다.
for book, before, after in [
    (cash_book, "시작현금", "마감현금"),
    (position_book, "시작수량", "마감수량"),
]:
    if book[before].iloc[1:].tolist() != book[after].iloc[:-1].tolist():
        raise ValueError("전날 마감과 다음 날 시작 상태가 연결되지 않습니다.")

for title, book in [
    ("주문 기록", orders),
    ("모의 체결 기록", fills),
    ("현금 장부", cash_book),
    ("보유수량 장부", position_book),
]:
    print(f"\n[{title}]")
    print(book.to_string(index=False))

print("\n주문·체결 연결 검사: 통과")
print("현금·수량 손계산 비교: 통과")
print("전날 마감·다음 날 시작 연결 검사: 통과")
print(f"최종 현금: {cash:,.0f}원")
print(f"최종 보유수량: {shares}주")

