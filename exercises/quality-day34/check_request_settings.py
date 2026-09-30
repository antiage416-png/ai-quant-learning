# 목적: 저장된 조회 조건이 KRX 일봉·수정주가 설정인지 확인합니다.
# 입력: 32·33일차 raw 폴더에 저장된 *_meta.json 파일
# 처리: params 안의 시장·주기·수정주가 요청값을 검사합니다.
# 출력: 종목별 검사 건수와 확인이 필요한 파일명
# API 요청과 파일 변경은 없으며, 인증 파일은 읽지 않습니다.

import json
from collections import Counter
from pathlib import Path


# 현재 코드 위치에서 저장소 루트와 검사할 폴더를 찾습니다.
ROOT = Path(__file__).resolve().parents[2]
RAW_DIRS = [
    ROOT / "data" / "stock-day32" / "raw",
    ROOT / "data" / "stock-day33" / "raw",
]

# 우리가 수집할 때 정한 요청 조건입니다.
EXPECTED = {
    "FID_COND_MRKT_DIV_CODE": "J",
    "FID_PERIOD_DIV_CODE": "D",
    "FID_ORG_ADJ_PRC": "0",
}
STOCK_CODES = {"005930", "000660", "005380", "035420", "055550"}

# Counter는 종목코드별로 검사한 파일 수를 누적합니다.
counts = Counter()
issues = []
checked = 0

for folder in RAW_DIRS:
    # 폴더가 없으면 검사를 생략하고 통과시키지 않습니다.
    if not folder.is_dir():
        issues.append(f"폴더 없음: {folder.relative_to(ROOT)}")
        continue

    # rglob는 하위 폴더까지 찾아 조회 조건 파일만 선택합니다.
    files = sorted(folder.rglob("*_meta.json"))
    if not files:
        issues.append(f"조회 조건 파일 없음: {folder.relative_to(ROOT)}")

    for path in files:
        checked += 1
        label = str(path.relative_to(ROOT))

        # 파일을 읽거나 JSON으로 해석할 수 없으면 문제로 기록합니다.
        # 파일 전체 내용은 출력하지 않습니다.
        try:
            meta = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            issues.append(f"{label}: 파일 읽기 또는 JSON 해석 실패")
            continue

        # 예상 구조가 아니면 실제 구조 확인이 필요하다고 표시합니다.
        if not isinstance(meta, dict):
            issues.append(f"{label}: 조회 조건 구조 확인 필요")
            continue

        params = meta.get("params")
        if not isinstance(params, dict):
            issues.append(f"{label}: params 항목 확인 필요")
            continue

        code = params.get("FID_INPUT_ISCD")
        if code not in STOCK_CODES:
            issues.append(f"{label}: 종목코드 확인 필요")
            continue

        counts[code] += 1

        # 항목이 없거나 기대한 값과 다르면 파일명과 항목명만 남깁니다.
        for field, expected in EXPECTED.items():
            if params.get(field) != expected:
                issues.append(f"{label}: {field} 확인 필요")

# 일부 종목의 파일만 있어도 전체 통과로 표시되지 않게 합니다.
for code in sorted(STOCK_CODES):
    if counts[code] == 0:
        issues.append(f"{code}: 검사 가능한 조회 조건 파일 없음")

print(f"찾은 조회 조건 파일 수: {checked}")
for code in sorted(STOCK_CODES):
    print(f"{code}: 검사한 조회 조건 {counts[code]}개")

if issues:
    print("\n요청 조건 검사: 확인 필요")
    for issue in issues:
        print(f"- {issue}")
else:
    print("\n요청 조건 검사: 통과")
    print("모든 검사 대상: KRX J / 일봉 D / 수정주가 요청값 0")

print("\n검사 범위: 저장된 요청 조건")
print("실제 가격 보정의 정확성: 이번 검사 대상 아님")