# 목적: 실제 다섯 종목을 합의한 세 구간으로 나누고 최종 평가 자료를 별도 보관합니다.
# 입력: 33일차 정리 CSV 5개와 기존 거래일 기준, 작은 예제의 구간 설정입니다.
# 처리: 날짜를 검사하고 분리·저장한 뒤 재읽기와 원본 복원을 검증합니다.
# 결과: 46일차 폴더에 구간별 CSV 15개와 분리 명세 JSON 1개를 저장합니다.
# 원본 데이터는 변경하지 않습니다. 인터넷 요청·실제 주문·성과 계산은 없습니다.

# hashlib는 파일 내용의 변경 여부를 비교하는 SHA-256 값을 계산합니다.
# io는 읽어 둔 원본 바이트를 pandas에 전달하고, json은 분리 명세를 저장합니다.
import hashlib
import io
import json
import sys
from pathlib import Path

import pandas as pd

from check_split import PERIODS, split_by_period


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "data" / "stock-day46"
STOCK_CODES = ["005930", "000660", "005380", "035420", "055550"]
EXPECTED_COUNTS = {"development": 118, "validation": 65, "final_evaluation": 59}

# 45일차에서 검증한 기존 달력 읽기와 날짜 검사 함수를 재사용합니다.
# 해당 모듈은 직접 실행할 때만 검사를 수행하므로 가져올 때 보고서를 저장하지 않습니다.
sys.path.insert(0, str(ROOT / "exercises" / "execution-day45"))
from check_saved_data import build_calendar
from check_calendar_rules import parse_dates, require_complete_dates


def digest(content):
    return hashlib.sha256(content).hexdigest()


# 종목코드의 앞자리 0과 원래 열의 문자열 값을 보존하며 CSV를 읽습니다.
def read_table(content):
    return pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False)


# 이미 있는 결과는 내용이 같을 때만 유지합니다. 다른 결과를 덮어쓰지 않습니다.
def check_existing(path, content):
    if path.exists() and path.read_bytes() != content:
        raise ValueError(f"내용이 다른 기존 결과가 있습니다. 먼저 확인해야 합니다: {path}")


def main():
    calendar = build_calendar()
    originals, sources, parts_by_code, planned_files = {}, {}, {}, {}
    file_records = []

    # 다섯 종목을 모두 검사하고 저장 내용을 준비한 다음에 파일 저장을 시작합니다.
    for code in STOCK_CODES:
        source_path = ROOT / "data" / "stock-day33" / "clean" / f"{code}_2025_clean.csv"
        original_bytes = source_path.read_bytes()
        frame = read_table(original_bytes)
        if not {"stock_code", "date", "open", "close"}.issubset(frame.columns):
            raise ValueError(f"필수 열이 없습니다: {code}")
        if not frame["stock_code"].eq(code).all():
            raise ValueError(f"종목코드가 다릅니다: {code}")
        require_complete_dates(parse_dates(frame["date"]), calendar)
        parts = split_by_period(frame)
        originals[source_path] = original_bytes
        sources[code] = {
            "path": source_path.relative_to(ROOT).as_posix(),
            "rows": len(frame), "sha256": digest(original_bytes),
        }
        parts_by_code[code] = (frame, parts)
        for key, part in parts.items():
            if len(part) != EXPECTED_COUNTS[key]:
                raise ValueError(f"합의한 구간의 예상 행 수와 다릅니다: {code}, {key}")
            path = OUTPUT / key / f"{code}_2025_clean.csv"
            content = part.to_csv(index=False, lineterminator="\n").encode("utf-8")
            # 실제 저장에 앞서 CSV 변환으로 값이나 열이 달라지지 않았는지도 검사합니다.
            pd.testing.assert_frame_equal(read_table(content), part.reset_index(drop=True))
            planned_files[path] = content
            file_records.append({
                "stock_code": code, "period": key,
                "path": path.relative_to(OUTPUT).as_posix(),
                "rows": len(part), "first_date": part["date"].iloc[0],
                "last_date": part["date"].iloc[-1], "sha256": digest(content),
            })

    # 명세에는 경계·행 수·파일 해시와 평가 자료 사용 범위를 함께 남깁니다.
    # 해시는 내용 변경을 발견하기 위한 값이며 파일 열람을 막는 잠금장치는 아닙니다.
    manifest = {
        "schema_version": 1,
        "periods": PERIODS,
        "source_data": sources,
        "files": file_records,
        "full_period_previously_viewed": True,
        "final_evaluation_policy": "규칙 확정 후 평가용으로 보관하며 개발·검증의 성과 비교에 사용하지 않는다.",
        "evaluation_limitation": "2025년 전체 그래프와 성과를 이미 확인했으므로 완전히 미관측인 독립 평가 자료로 주장하지 않는다.",
        "indicator_note": "지표 계산은 수행하지 않았다. 이후 과거 준비 구간과 평가 대상 구간을 구분하고 미래 자료를 사용하지 않아야 한다.",
    }
    manifest_path = OUTPUT / "split_manifest.json"
    planned_files[manifest_path] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    # 하나라도 기존 결과와 충돌하면 새 결과를 쓰기 전에 중단합니다.
    for path, content in planned_files.items():
        check_existing(path, content)
    for path, content in originals.items():
        if path.read_bytes() != content:
            raise ValueError(f"검사 도중 입력 파일이 변경되었습니다: {path}")

    created, kept = 0, 0
    for path, content in planned_files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        check_existing(path, content)
        if path.exists():
            kept += 1
        else:
            # xb는 새 파일만 만들고 기존 파일이 생겼다면 오류로 멈추는 모드입니다.
            with path.open("xb") as handle:
                handle.write(content)
            created += 1

    # 디스크의 CSV를 다시 읽고 모든 열·행을 비교합니다. 가격이나 성과를 화면에 출력하지 않습니다.
    for code, (original, parts) in parts_by_code.items():
        restored_parts = []
        for key, part in parts.items():
            path = OUTPUT / key / f"{code}_2025_clean.csv"
            content = path.read_bytes()
            if digest(content) != digest(planned_files[path]):
                raise ValueError(f"저장한 파일의 내용이 다릅니다: {path}")
            reread = read_table(content)
            pd.testing.assert_frame_equal(reread, part.reset_index(drop=True))
            restored_parts.append(reread)
        pd.testing.assert_frame_equal(pd.concat(restored_parts, ignore_index=True), original.reset_index(drop=True))
        print(f"{code}: 개발 118행 / 검증 65행 / 최종 평가 59행 / 합계 242행")
    if json.loads(manifest_path.read_text(encoding="utf-8")) != manifest:
        raise ValueError("분리 명세 재읽기 결과가 다릅니다.")
    if any(path.read_bytes() != content for path, content in originals.items()):
        raise ValueError("입력 파일의 변경이 발견되었습니다.")

    print("\n기존 거래일 기준 대조·구간별 행 수 검사: 통과")
    print("구간 간 중복 없음·전체 행 보존 검사: 통과")
    print("저장 CSV 재읽기·재결합 원본 복원 검사: 통과")
    print("원본 파일 보존·분리 명세 재읽기 검사: 통과")
    print(f"구간별 CSV: {len(file_records)}개 / 분리 명세: 1개")
    print(f"새로 저장: {created}개 / 동일한 기존 파일 유지: {kept}개")
    for key, period in PERIODS.items():
        print(f"{period['label']} 저장 폴더: {OUTPUT / key}")
    print(f"분리 명세: {manifest_path}")
    print("최종 평가 자료는 개발·검증의 성과 비교에 사용하지 않습니다.")
    print("이미 확인한 2025년 자료이므로 완전히 미관측인 독립 평가 자료는 아닙니다.")
    print("인터넷 요청·실제 주문·성과 계산: 없음")


if __name__ == "__main__":
    main()
