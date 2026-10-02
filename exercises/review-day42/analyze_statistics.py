# 목적: 같은 거래일의 5종목 수익률 통계와 상관관계를 확인합니다.
# 입력: 33일차에서 저장하고 검증한 종목별 종가 CSV
# 처리: 날짜 정렬·일치 확인 → 수익률 계산 → 통계·상관관계 계산
# 출력: 통계 CSV, 상관관계 CSV, 수익률 CSV, Markdown 보고서
# API 요청은 없으며 기존 입력 CSV는 변경하지 않습니다.

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = ROOT / "data" / "stock-day33" / "clean"
OUTPUT_DIR = ROOT / "data" / "stock-day42"
REPORT_PATH = Path(__file__).resolve().with_name("statistics_report.md")

STOCKS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "005380": "현대차",
    "035420": "NAVER",
    "055550": "신한지주",
}

price_series = {}

for code, name in STOCKS.items():
    path = INPUT_DIR / f"{code}_2025_clean.csv"
    table = pd.read_csv(path, dtype=str, keep_default_na=False)

    if len(table) < 3:
        raise ValueError(f"{name}: 표본분산 계산에 필요한 가격이 부족합니다.")

    if not table["stock_code"].eq(code).all():
        raise ValueError(f"{name}: 종목코드가 다릅니다.")

    if not table["market"].eq("KRX").all():
        raise ValueError(f"{name}: 시장 정보가 다릅니다.")

    table["date"] = pd.to_datetime(
        table["date"], format="%Y-%m-%d", errors="raise"
    )
    table["close"] = pd.to_numeric(table["close"], errors="raise")

    if table["date"].isna().any() or table["date"].duplicated().any():
        raise ValueError(f"{name}: 날짜 결측 또는 중복이 있습니다.")

    if (
        table["close"].isna().any()
        or table["close"].le(0).any()
        or table["close"].isin([float("inf"), float("-inf")]).any()
    ):
        raise ValueError(f"{name}: 유효하지 않은 종가가 있습니다.")

    # 날짜를 행의 이름인 인덱스로 사용하고 시간순으로 정렬합니다.
    price_series[code] = table.set_index("date")["close"].sort_index()

# 날짜가 다르면 일부 날짜를 조용히 버리지 않고 실행을 중단합니다.
reference_dates = price_series["005930"].index
for code, values in price_series.items():
    if not values.index.equals(reference_dates):
        raise ValueError(f"{code}: 다른 종목과 거래일이 다릅니다.")

# 날짜별 종가를 종목별 열로 나란히 모읍니다.
prices = pd.DataFrame(price_series)

all_returns = prices.pct_change(fill_method=None)

# 첫 행은 이전 가격이 없어 모든 종목의 수익률이 결측이어야 합니다.
if not all_returns.iloc[0].isna().all():
    raise ValueError("첫날 수익률의 결측 상태를 확인해야 합니다.")

# 첫 행만 제외합니다. 다른 결측값은 임의로 제거하지 않습니다.
returns = all_returns.iloc[1:].copy()
if (
    returns.isna().any().any()
    or returns.isin([float("inf"), float("-inf")]).any().any()
):
    raise ValueError("첫날 이후 수익률에 결측값 또는 무한대가 있습니다.")

summary_rows = []

for code, name in STOCKS.items():
    values = returns[code]
    count = len(values)
    positive = int(values.gt(0).sum())
    negative = int(values.lt(0).sum())
    zero = int(values.eq(0).sum())

    if positive + negative + zero != count:
        raise ValueError(f"{name}: 수익률 관측 개수가 맞지 않습니다.")

    summary_rows.append({
        "stock_code": code,
        "name": name,
        "return_count": count,
        "positive_count": positive,
        "negative_count": negative,
        "zero_count": zero,
        # 0인 날도 전체 관측 수인 분모에 포함합니다.
        "positive_rate": positive / count,
        "mean_return": values.mean(),
        "sample_variance": values.var(ddof=1),
        "sample_std": values.std(ddof=1),
        "cumulative_return": prices[code].iloc[-1] / prices[code].iloc[0] - 1,
    })

summary = pd.DataFrame(summary_rows)

# 표준편차가 0인 자료의 상관계수는 정의되지 않을 수 있습니다.
# 그런 결과를 0으로 채워 관계가 없다는 뜻으로 바꾸지 않습니다.
if returns.nunique().lt(2).any():
    raise ValueError("수익률 변화가 없는 종목이 있어 상관관계를 확인해야 합니다.")

correlations = returns.corr(method="pearson")
if correlations.isna().any().any():
    raise ValueError("계산할 수 없는 상관계수가 있습니다.")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
summary.to_csv(OUTPUT_DIR / "returns_statistics.csv", index=False)
correlations.to_csv(OUTPUT_DIR / "return_correlations.csv", index_label="stock_code")
returns.to_csv(OUTPUT_DIR / "daily_returns.csv", index_label="date")

# 표시할 때만 비율을 퍼센트로 변환합니다.
display = summary[[
    "name", "return_count", "positive_rate",
    "mean_return", "sample_std", "cumulative_return",
]].copy()

for column in [
    "positive_rate", "mean_return", "sample_std", "cumulative_return"
]:
    display[column] *= 100

display = display.rename(columns={
    "name": "종목",
    "return_count": "관측수",
    "positive_rate": "상승비율(%)",
    "mean_return": "평균(%)",
    "sample_std": "표준편차(%)",
    "cumulative_return": "기간수익률(%)",
})

# 추가 패키지 없이 Markdown 표를 직접 만듭니다.
report = [
    "# 42일차 실제 수익률 통계",
    "",
    f"- 가격 기준일: {prices.index[0]:%Y-%m-%d}",
    f"- 첫 수익률 날짜: {returns.index[0]:%Y-%m-%d}",
    f"- 마지막 날짜: {returns.index[-1]:%Y-%m-%d}",
    f"- 종목별 가격 수: {len(prices)}개",
    f"- 종목별 수익률 수: {len(returns)}개",
    "",
    "## 종목별 통계",
    "",
    "| 종목 | 상승일 비율(%) | 일간 평균(%) | 표본분산 | 일간 표준편차(%) | 기간수익률(%) |",
    "|---|---:|---:|---:|---:|---:|",
]

for row in summary.itertuples(index=False):
    report.append(
        f"| {row.name} | {row.positive_rate * 100:.4f}"
        f" | {row.mean_return * 100:.4f} | {row.sample_variance:.8f}"
        f" | {row.sample_std * 100:.4f}"
        f" | {row.cumulative_return * 100:.4f} |"
    )

codes = list(STOCKS)
report.extend([
    "",
    "## 일간수익률 상관계수",
    "",
    "| 종목코드 | " + " | ".join(codes) + " |",
    "|---|" + "---:|" * len(codes),
])

for code in codes:
    values = [f"{correlations.loc[code, other]:.4f}" for other in codes]
    report.append("| " + code + " | " + " | ".join(values) + " |")

report.extend([
    "",
    "## 해석 기준",
    "",
    "- 상승일 비율은 관측 빈도이며 미래 상승 확률을 확정하지 않는다.",
    "- 평균·분산·표준편차는 일간수익률 기준이며 연율화하지 않았다.",
    "- 표본분산은 소수 수익률의 제곱 단위다.",
    "- 기간수익률은 첫 종가 대비 마지막 종가의 변화율이다.",
    "- 상관계수는 같은 날짜의 수익률로 계산한 선형 관계다.",
    "- 상관관계는 인과관계나 동일한 수익률 크기를 뜻하지 않는다.",
    "- 이번 결과는 관측한 종목과 기간에 한정된다.",
])

REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")

print(f"종목별 가격 수: {len(prices)}개")
print(f"종목별 수익률 수: {len(returns)}개")
print(f"가격 기준일: {prices.index[0]:%Y-%m-%d}")
print(f"첫 수익률 날짜: {returns.index[0]:%Y-%m-%d}")

print("\n종목별 통계:")
print(display.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

print("\n같은 날짜의 일간수익률 상관계수:")
print(correlations.to_string(float_format=lambda x: f"{x:.4f}"))

print("\n종목별 날짜 일치·수익률 결측 검사: 통과")
print(f"통계 CSV 저장 폴더: {OUTPUT_DIR}")
print(f"보고서 저장: {REPORT_PATH}")