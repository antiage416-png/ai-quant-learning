# 목적:
# 종목별 CSV의 결측·중복·날짜·가격·거래량을 검사합니다.
#
# 흐름:
# CSV 읽기 → 검사별 건수 계산 → 종목 간 날짜 비교 → 보고서 저장
#
# 실행 영향:
# 인터넷 요청과 원본 CSV 변경은 없습니다.
# 이 코드와 같은 폴더의 quality_report.md를 생성하거나 덮어씁니다.
# 보고서에는 실제 가격이나 인증정보를 기록하지 않습니다.

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = ROOT / "data/stock-day33/clean"
REPORT_PATH = Path(__file__).resolve().parent / "quality_report.md"

CODES = ["005930", "000660", "005380", "035420", "055550"]
COLUMNS = [
    "stock_code", "market", "date",
    "open", "high", "low", "close", "volume",
]
NUMBER_COLUMNS = ["open", "high", "low", "close", "volume"]
PRICE_COLUMNS = ["open", "high", "low", "close"]


def main():
    """검사 결과를 출력하고 Markdown 보고서로 저장합니다."""

    results = []
    date_sets = {}

    for code in CODES:
        # 처음에는 문자열 그대로 읽어 빈값과 변환 오류를 구분합니다.
        table = pd.read_csv(
            INPUT_DIR / f"{code}_2025_clean.csv",
            dtype=str,
            keep_default_na=False,
        )

        if table.columns.tolist() != COLUMNS:
            raise ValueError(f"{code}: 열 이름 또는 순서가 다릅니다.")

        # 검사에 사용할 복사본의 앞뒤 공백만 정리합니다.
        # CSV 파일의 값은 변경하지 않습니다.
        text = table.apply(lambda column: column.str.strip())
        blank = text.eq("")

        # errors="coerce"는 해석할 수 없는 값을 결측으로 표시합니다.
        # 아래에서 원래 빈값과 비교해 변환 오류를 따로 셉니다.
        dates = pd.to_datetime(
            text["date"], format="%Y-%m-%d", errors="coerce"
        )
        numbers = text[NUMBER_COLUMNS].apply(
            pd.to_numeric, errors="coerce"
        )

        date_errors = dates.isna() & ~blank["date"]
        number_errors = numbers.isna() & ~blank[NUMBER_COLUMNS]

        # 가격이 모두 존재하는 행에 대해서만 가격 관계를 검사합니다.
        # 가격이 없는 행은 필수 빈값·변환 오류 항목에서 확인합니다.
        complete_prices = numbers[PRICE_COLUMNS].notna().all(axis=1)
        valid_prices = (
            (numbers["low"] <= numbers["high"])
            & numbers["open"].between(numbers["low"], numbers["high"])
            & numbers["close"].between(numbers["low"], numbers["high"])
        )

        results.append({
            "종목코드": code,
            "행수": len(table),
            "필수빈칸": int(blank.sum().sum()),
            "중복행": int(
                text.duplicated(["stock_code", "market", "date"]).sum()
            ),
            "종목불일치": int(text["stock_code"].ne(code).sum()),
            "시장불일치": int(text["market"].ne("KRX").sum()),
            "날짜변환오류": int(date_errors.sum()),
            "기간밖날짜": int(
                (dates.notna() & ~dates.between(
                    "2025-01-01", "2025-12-31"
                )).sum()
            ),
            "주말날짜": int(dates.dt.dayofweek.ge(5).sum()),
            "숫자변환오류": int(number_errors.sum().sum()),
            "정수아닌값": int(
                ((numbers % 1).ne(0) & numbers.notna()).sum().sum()
            ),
            "음수값": int(numbers.lt(0).sum().sum()),
            "가격관계이상행": int(
                (complete_prices & ~valid_prices).sum()
            ),
            "가격0행": int(numbers[PRICE_COLUMNS].eq(0).any(axis=1).sum()),
            "거래량0행": int(numbers["volume"].eq(0).sum()),
        })

        # 올바르게 해석된 날짜만 비교 집합에 넣습니다.
        # 제외된 날짜 오류는 위 검사 건수에 별도로 남습니다.
        date_sets[code] = set(
            dates.dropna().dt.strftime("%Y-%m-%d")
        )

    summary = pd.DataFrame(results)
    print(summary.to_string(index=False))

    union_dates = set.union(*date_sets.values())
    common_dates = set.intersection(*date_sets.values())

    # 별도 표 출력 패키지 없이 Markdown 표를 만듭니다.
    headers = summary.columns.tolist()
    lines = [
        "# 34일차 — 주가 CSV 품질 점검",
        "",
        "검사 대상: 2025년 KRX 일별 수정주가 CSV 5개.",
        "검사 과정에서 원본 CSV를 변경하지 않았다.",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for row in summary.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value) for value in row) + " |")

    lines.extend([
        "",
        "## 날짜 비교",
        f"- 날짜 합집합: {len(union_dates)}개",
        f"- 모든 종목 공통 날짜: {len(common_dates)}개",
    ])

    for code in CODES:
        missing_count = len(union_dates - date_sets[code])
        lines.append(f"- {code}: 다른 종목 대비 없는 날짜 {missing_count}개")

    lines.extend([
        "",
        "## 해석 기준",
        "- 필수빈칸·숫자변환오류·정수아닌값·음수값은 셀 개수다.",
        "- 중복행은 첫 행을 제외한 추가 중복 행 수다.",
        "- 가격 또는 거래량 0은 원인 확인 대상이며 자동 오류 판정이 아니다.",
        "- 검사 건수는 서로 겹칠 수 있으므로 모두 더해 오류 행 수로 해석하지 않는다.",
        "- 종목 간 날짜 일치는 공식 거래일의 완전성을 보장하지 않는다.",
        "",
        "## 아직 확인하지 않은 사항",
        "- 공식 거래일 달력과의 대조",
        "- 수정주가 조정 범위와 주식분할 관련 확인",
    ])

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n날짜 합집합:", len(union_dates))
    print("공통 날짜:", len(common_dates))
    print("보고서 저장:", REPORT_PATH)


if __name__ == "__main__":
    main()