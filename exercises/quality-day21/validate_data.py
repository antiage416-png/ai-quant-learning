from pathlib import Path
import pandas as pd

# 14일차에 저장한 통합 CSV를 사용합니다.
current_dir = Path(__file__).resolve().parent
csv_path = (
    current_dir.parent
    / "validation-day14"
    / "quotes_two_pages.csv"
)

# 문자열로 읽고, 빈 칸도 빈 문자열로 유지합니다.
df = pd.read_csv(
    csv_path,
    encoding="utf-8-sig",
    dtype=str,
    keep_default_na=False,
)

# 반드시 값이 있어야 하는 열입니다.
required_columns = [
    "text",
    "author",
    "source_url",
    "collected_at",
]

print("검사 대상 행 수:", len(df))

for column in required_columns:
    # 앞뒤 공백을 제거한 결과가 빈 문자열인지 확인합니다.
    empty_mask = df[column].str.strip().eq("")

    # True인 항목의 개수를 셉니다.
    empty_count = int(empty_mask.sum())

    print(f"{column} 빈값: {empty_count}")

# 발표 시각은 원문에 없었으므로 별도로 확인합니다.
published_empty = df["published_at"].str.strip().eq("")
print("발표 시각 미제공:", int(published_empty.sum()))

# 본문과 작성자가 같은 행을 중복으로 판단합니다.
# 같은 조합의 첫 번째 행은 남겨두고, 이후 행을 True로 표시합니다.
duplicate_mask = df.duplicated(
    subset=["text", "author"],
    keep="first",
)

duplicate_count = int(duplicate_mask.sum())
print("중복 명언 수:", duplicate_count)

# 중복이 있을 때만 해당 행의 본문과 작성자를 보여줍니다.
if duplicate_count > 0:
    print(df.loc[duplicate_mask, ["text", "author"]].to_string(index=False))

# 나중에 보고서에 넣을 날짜 오류 개수를 모읍니다.
date_errors = {}

for column in ["collected_at", "published_at"]:
    # 앞뒤 공백을 제거합니다.
    values = df[column].str.strip()

    # 빈값이 아닌 항목만 날짜 검사 대상으로 삼습니다.
    has_value = values.ne("")

    # ISO 형식의 날짜·시각으로 변환합니다.
    # 변환할 수 없으면 오류로 중단하지 않고 NaT로 표시합니다.
    parsed = pd.to_datetime(
        values,
        format="ISO8601",
        errors="coerce",
        utc=True,
    )

    # 값은 있는데 날짜로 변환되지 않은 항목을 찾습니다.
    invalid_mask = has_value & parsed.isna()

    invalid_count = int(invalid_mask.sum())
    date_errors[column] = invalid_count

    print(f"{column} 날짜 형식·유효성 오류: {invalid_count}")

# 보고서에 넣을 필수 항목별 빈값 개수를 정리합니다.
required_empty_counts = {
    column: int(df[column].str.strip().eq("").sum())
    for column in required_columns
}

# 이번 검사 범위에서 발견한 문제가 있는지 판단합니다.
has_issues = (
    any(count > 0 for count in required_empty_counts.values())
    or duplicate_count > 0
    or any(count > 0 for count in date_errors.values())
)

result = "확인 필요" if has_issues else "검사 항목 통과"

# Markdown 보고서를 한 줄씩 구성합니다.
lines = [
    "# 데이터 품질 검증 보고서",
    "",
    f"- 검사 파일: `{csv_path.name}`",
    f"- 검사 대상: {len(df)}행",
    f"- 결과: {result}",
    "",
    "| 검사 항목 | 건수 |",
    "|---|---:|",
]

for column, count in required_empty_counts.items():
    lines.append(f"| {column} 빈값 | {count} |")

lines.append(f"| 중복 명언 | {duplicate_count} |")

for column, count in date_errors.items():
    lines.append(f"| {column} 날짜 형식·유효성 오류 | {count} |")

lines.extend([
    "",
    f"- 발표 시각 미제공: {int(published_empty.sum())}건",
    "- 발표 시각의 빈값은 날짜 오류에서 제외했습니다.",
    "- 중복 기준은 본문과 작성자의 정확한 일치입니다.",
    "- 날짜 검사는 해석 가능 여부만 확인합니다.",
    "- 원문 일치 여부와 실제 시각의 정확성은 이번 자동 검사에 포함하지 않습니다.",
])

# 줄들을 연결해 파일에 저장합니다. 기존 보고서는 덮어씁니다.
report_path = current_dir / "quality_report.md"
report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

print("보고서 저장:", report_path)