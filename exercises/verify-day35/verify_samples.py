# 목적: 종목별 첫날·마지막 날, 총 10건의 CSV 값을 원본과 대조합니다.
# 입력: 33일차 CSV와 상태 파일, 32·33일차의 저장된 원본 JSON
# 처리: 같은 날짜의 원본 행을 찾아 가격 4개와 거래량을 비교합니다.
# 출력: 터미널 요약과 sample_report.md
# API 요청은 없으며, 기존 데이터는 변경하지 않습니다.

import json
from decimal import Decimal
from pathlib import Path

import pandas as pd


# 코드 위치를 기준으로 저장소와 입력 파일의 위치를 정합니다.
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "stock-day33"
REPORT_PATH = Path(__file__).resolve().with_name("sample_report.md")

STOCK_CODES = ["005930", "000660", "005380", "035420", "055550"]

# 왼쪽은 CSV 열 이름, 오른쪽은 한국투자증권 원본 필드 이름입니다.
FIELDS = {
    "open": "stck_oprc",
    "high": "stck_hgpr",
    "low": "stck_lwpr",
    "close": "stck_clpr",
    "volume": "acml_vol",
}


def read_json(path):
    # 파일 내용을 문자열로 읽은 뒤 Python 자료형으로 변환합니다.
    return json.loads(path.read_text(encoding="utf-8"))


def get_raw_paths(info):
    # 삼성전자는 기존 CSV 이름에서 당시 연간 원본 폴더를 찾습니다.
    # 예: 005930_2025_수집시각_clean.csv → 005930_2025_수집시각
    if info.get("existing_csv"):
        existing_csv = Path(info["existing_csv"])
        if not existing_csv.is_file():
            raise FileNotFoundError("재사용한 기존 CSV가 없습니다.")

        run_name = existing_csv.name.removesuffix("_clean.csv")
        raw_dir = ROOT / "data" / "stock-day32" / "raw" / run_name

        # 조회 조건과 완료 목록을 제외하고 응답 JSON만 선택합니다.
        paths = sorted(
            path
            for path in raw_dir.glob("*.json")
            if path.name != "manifest.json"
            and not path.name.endswith("_meta.json")
        )
    else:
        # 나머지 종목은 상태에 기록된 원본 경로를 그대로 사용합니다.
        paths = [
            DATA_DIR / batch["raw_file"]
            for batch in info["batches"]
        ]

    # 연간 월별 원본 12개가 있어야 이번 실습을 계속합니다.
    if len(paths) != 12 or len(set(paths)) != 12:
        raise ValueError("서로 다른 월별 원본 12개인지 확인해야 합니다.")

    return paths


state = read_json(DATA_DIR / "state.json")
report = [
    "# 35일차 원본·CSV 샘플 대조",
    "",
    "- 공급원: 한국투자증권 Open API",
    "- 대상 기간: 2025년",
    "- 표본 선택: 종목별 CSV의 첫 거래일과 마지막 거래일",
    "- 비교 항목: 시가·고가·저가·종가·거래량",
    "- 비교 범위: 저장된 공급원 응답과 CSV 사이의 일치 여부",
    "- 다른 공급원과의 교차 검증이나 현재 API 재조회는 수행하지 않음",
    "",
]

sample_count = 0
matched_count = 0

for code in STOCK_CODES:
    csv_path = DATA_DIR / "clean" / f"{code}_2025_clean.csv"

    # 문자열로 읽어 종목코드 앞자리 0과 저장된 숫자 표현을 보존합니다.
    table = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    if len(table) < 2 or not table["stock_code"].eq(code).all():
        raise ValueError(f"{code}: 행 수 또는 종목코드를 확인해야 합니다.")

    # 날짜를 해석해 정렬하고 첫 행과 마지막 행을 선택합니다.
    table["date"] = pd.to_datetime(
        table["date"], format="%Y-%m-%d", errors="raise"
    )
    table = table.sort_values("date")
    if table["date"].duplicated().any():
        raise ValueError(f"{code}: 중복 날짜가 있습니다.")

    samples = table.iloc[[0, -1]]

    # 원본을 한 번씩 읽고, 날짜별로 원본 행과 파일 경로를 모읍니다.
    # 같은 날짜가 여러 원본에 있으면 뒤에서 확인 필요로 처리합니다.
    originals = {}
    for raw_path in get_raw_paths(state["stocks"][code]):
        payload = read_json(raw_path)
        if payload.get("rt_cd") != "0":
            raise ValueError(f"{code}: 성공 응답이 아닌 원본입니다.")

        rows = payload.get("output2")
        if not isinstance(rows, list):
            raise ValueError(f"{code}: 원본의 output2 구조를 확인해야 합니다.")

        for row in rows:
            raw_date = str(row.get("stck_bsop_date", "")).strip()
            if raw_date:
                originals.setdefault(raw_date, []).append((row, raw_path))

    for _, sample in samples.iterrows():
        date_text = sample["date"].strftime("%Y-%m-%d")
        raw_date = sample["date"].strftime("%Y%m%d")
        candidates = originals.get(raw_date, [])

        # 원본이 없거나 여러 개면 임의로 선택하지 않고 실행을 멈춥니다.
        if len(candidates) != 1:
            raise ValueError(
                f"{code} {date_text}: 대응 원본이 {len(candidates)}개입니다."
            )

        original, raw_path = candidates[0]
        comparisons = []

        for column, raw_field in FIELDS.items():
            # Decimal로 비교하면 "100"과 "100.0"을 같은 수로 판단하면서
            # 부동소수점 변환에 따른 오차를 피할 수 있습니다.
            csv_value = Decimal(str(sample[column]).strip())
            raw_value = Decimal(str(original[raw_field]).strip())
            same = (
                csv_value.is_finite()
                and raw_value.is_finite()
                and csv_value == raw_value
            )
            comparisons.append((column, csv_value, raw_value, same))

        matched = all(item[3] for item in comparisons)
        sample_count += 1
        matched_count += int(matched)
        result = "일치" if matched else "불일치"

        print(f"{code} {date_text}: {result}")
        report.extend([
            f"## {code} / {date_text}",
            "",
            f"- CSV: `{csv_path.relative_to(ROOT)}`",
            f"- 원본: `{raw_path.relative_to(ROOT)}`",
            f"- 결과: {result}",
            "",
            "| 항목 | CSV | 원본 | 결과 |",
            "|---|---:|---:|---|",
        ])

        for column, csv_value, raw_value, same in comparisons:
            label = "일치" if same else "불일치"
            report.append(
                f"| {column} | {csv_value} | {raw_value} | {label} |"
            )
        report.append("")

# 모든 종목을 처리한 뒤 표본 개수를 확인하고 보고서를 저장합니다.
if sample_count != 10:
    raise ValueError(f"표본이 10건인지 확인해야 합니다: {sample_count}건")

report.extend([
    "## 전체 결과",
    "",
    f"- 비교한 표본: {sample_count}건",
    f"- 일치: {matched_count}건",
    f"- 불일치: {sample_count - matched_count}건",
    "- 표본 결과를 전체 1,210행의 값 검증 결과로 확대 해석하지 않는다.",
])

REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")

print(f"\n표본: {sample_count}건")
print(f"일치: {matched_count}건")
print(f"불일치: {sample_count - matched_count}건")
print(f"보고서 저장: {REPORT_PATH}")