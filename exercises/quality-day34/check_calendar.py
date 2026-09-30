# 목적: 2025년 거래일 기준과 종목별 CSV 날짜를 비교합니다.
# 입력: 33일차에서 저장한 종목별 CSV 5개
# 처리: 평일에서 휴장일을 제외하고, 실제 날짜와 차이를 계산합니다.
# 출력: 터미널 결과와 calendar_report.md
# API 요청은 없으며, 원본 데이터와 기존 CSV는 변경하지 않습니다.

from pathlib import Path

import pandas as pd


# 현재 코드의 위치를 기준으로 저장소와 데이터 경로를 찾습니다.
ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = ROOT / "data" / "stock-day33" / "clean"
REPORT_PATH = Path(__file__).resolve().with_name("calendar_report.md")

STOCK_CODES = ["005930", "000660", "005380", "035420", "055550"]

# 2025년 평일에 해당하는 휴장일입니다.
# 주말은 아래 bdate_range에서 이미 제외하므로 중복해서 넣지 않습니다.
# 이 목록은 2025년 전용이며, 다른 연도에 그대로 사용하면 안 됩니다.
HOLIDAYS = {
    "2025-01-01": "신정",
    "2025-01-27": "임시공휴일",
    "2025-01-28": "설 연휴",
    "2025-01-29": "설날",
    "2025-01-30": "설 연휴",
    "2025-03-03": "삼일절 대체공휴일",
    "2025-05-01": "근로자의 날",
    "2025-05-05": "어린이날·부처님오신날",
    "2025-05-06": "대체공휴일",
    "2025-06-03": "대통령 선거일",
    "2025-06-06": "현충일",
    "2025-08-15": "광복절",
    "2025-10-03": "개천절",
    "2025-10-06": "추석",
    "2025-10-07": "추석 연휴",
    "2025-10-08": "추석 대체공휴일",
    "2025-10-09": "한글날",
    "2025-12-25": "성탄절",
    "2025-12-31": "연말 휴장일",
}

# bdate_range는 기본적으로 월요일부터 금요일까지 생성합니다.
# 한국의 공휴일까지 자동으로 제외해 주지는 않습니다.
weekdays = pd.bdate_range("2025-01-01", "2025-12-31")

# 날짜를 같은 문자열 형식으로 통일하고 집합으로 만듭니다.
# 집합의 뺄셈은 왼쪽에만 있는 날짜를 찾습니다.
weekday_dates = set(weekdays.strftime("%Y-%m-%d"))
expected_dates = weekday_dates - set(HOLIDAYS)

print(f"2025년 평일 수: {len(weekday_dates)}")
print(f"평일 휴장일 수: {len(HOLIDAYS)}")
print(f"대조 기준 거래일 수: {len(expected_dates)}")

report = [
    "# 34일차 거래일 대조 결과",
    "",
    "2025년 공휴일 안내와 KRX 휴장일 규정을 바탕으로 구성한 기준입니다.",
    "KRX에서 직접 내려받은 거래일 달력 파일은 아닙니다.",
    "",
    f"- 평일 수: {len(weekday_dates)}",
    f"- 평일 휴장일 수: {len(HOLIDAYS)}",
    f"- 대조 기준 거래일 수: {len(expected_dates)}",
    "",
]

all_match = True

for code in STOCK_CODES:
    # 종목코드의 앞자리 0을 보존하도록 문자열로 읽습니다.
    csv_path = INPUT_DIR / f"{code}_2025_clean.csv"
    table = pd.read_csv(csv_path, dtype=str, keep_default_na=False)

    # 날짜 변환에 실패하면 실행을 멈춥니다.
    # 잘못된 날짜를 조용히 제외한 채 통과시키지 않습니다.
    dates = pd.to_datetime(
        table["date"], format="%Y-%m-%d", errors="raise"
    )
    actual_dates = set(dates.dt.strftime("%Y-%m-%d"))

    # 있어야 하는데 없는 날짜와, 기준에 없는 날짜를 따로 구합니다.
    missing = sorted(expected_dates - actual_dates)
    unexpected = sorted(actual_dates - expected_dates)

    # 집합은 중복을 제거하므로 중복 날짜 수도 별도로 확인합니다.
    duplicate_count = int(dates.duplicated().sum())
    matched = not missing and not unexpected and duplicate_count == 0
    all_match = all_match and matched

    result = "일치" if matched else "확인 필요"
    print(
        f"\n{code}: {len(table)}행, 고유 날짜 {len(actual_dates)}개"
        f", 대조 결과: {result}"
    )
    print(f"  기준 대비 없는 날짜: {missing}")
    print(f"  기준에 없는 날짜: {unexpected}")
    print(f"  중복 날짜 수: {duplicate_count}")

    report.extend([
        f"## {code}",
        "",
        f"- 행 수: {len(table)}",
        f"- 고유 날짜 수: {len(actual_dates)}",
        f"- 기준 대비 없는 날짜: {missing}",
        f"- 기준에 없는 날짜: {unexpected}",
        f"- 중복 날짜 수: {duplicate_count}",
        f"- 대조 결과: {result}",
        "",
    ])

# 재검토할 수 있도록 사용한 휴장일과 근거를 보고서에도 남깁니다.
report.extend(["## 대조에 사용한 휴장일", ""])
for date, reason in HOLIDAYS.items():
    report.append(f"- {date}: {reason}")

report.extend([
    "",
    "## 참고 자료와 해석 범위",
    "",
    "- [관세청 공휴일 안내](https://customs.go.kr/engportal/cm/cntnts/cntntsView.do?cntntsId=7401&mi=13284)",
    "- [KRX 휴장일 규정](https://global.krx.co.kr/contents/GLB/06/0602/0602020204/GLB0602020204T1.jsp)",
    "- 날짜 일치는 가격·거래량의 정확성까지 보장하지 않습니다.",
    "- 거래정지 등 개별 종목 사유가 있다면 누락 날짜를 별도로 조사해야 합니다.",
])

# 이번 보고서만 저장합니다. 재실행하면 같은 보고서를 갱신합니다.
REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")

print(f"\n전체 날짜 대조: {'일치' if all_match else '확인 필요'}")
print(f"보고서 저장: {REPORT_PATH}")