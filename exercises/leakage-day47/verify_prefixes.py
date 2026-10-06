# 목적: 삼성전자 개발·검증 자료에서 미래 행 추가 전후의 과거 신호를 검사합니다.
# 입력: 46일차 개발·검증 CSV와 분리 명세, 40일차 신호 CSV의 앞 183행입니다.
# 처리: 기존 신호 대조와 앞 20~182행 재계산을 수행하고 입력 보존을 확인합니다.
# 결과: 실습 폴더의 보고서와 로컬 결과 폴더의 요약 JSON을 저장합니다.
# 최종 평가 CSV는 읽지 않습니다. 인터넷 요청·주문·수익률 계산은 없습니다.

import hashlib
import io
import json
import sys
from pathlib import Path

import pandas as pd

from check_prefix import calculate_signals, find_changed_prefixes


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "exercises/execution-day45"))
from check_saved_data import build_calendar
from check_calendar_rules import parse_dates, require_complete_dates


def digest(content):
    return hashlib.sha256(content).hexdigest()


# 행 수를 제한해 저장된 과거 결과만 대조용 표로 읽습니다.
# 40일차 전체 파일을 실행하거나 전체 기간을 표로 읽지 않습니다.
def read_reference(path, rows):
    frame = pd.read_csv(path, nrows=rows, dtype={"stock_code": str}, keep_default_na=False)
    required = {"stock_code", "date", "ma_5", "ma_20", "close_signal", "previous_signal"}
    if not required.issubset(frame.columns) or len(frame) != rows:
        raise ValueError("40일차 앞부분의 열 또는 행 수가 예상과 다릅니다.")
    if not frame["stock_code"].eq("005930").all():
        raise ValueError("40일차 종목코드가 다릅니다.")
    return frame


# 서로 다른 기존 결과를 덮어쓰지 않고, 같은 내용이면 유지합니다.
def check_existing(path, content):
    if path.exists() and path.read_bytes() != content:
        raise ValueError(f"다른 내용의 기존 결과가 있습니다. 확인이 필요합니다: {path}")


def main():
    split_root = ROOT / "data/stock-day46"
    manifest_path = split_root / "split_manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    calendar = build_calendar()
    expected_dates = calendar[calendar <= pd.Timestamp("2025-09-30")]
    frames, inputs = [], {manifest_path: manifest_bytes}

    # 두 폴더만 명시적으로 읽습니다. 최종 평가 폴더를 포함하는 일괄 검색은 하지 않습니다.
    for key, count, start, end in (
        ("development", 118, "2025-01-02", "2025-06-30"),
        ("validation", 65, "2025-07-01", "2025-09-30"),
    ):
        relative = f"{key}/005930_2025_clean.csv"
        path = split_root / relative
        content = path.read_bytes()
        matches = [row for row in manifest["files"] if row["path"] == relative]
        if len(matches) != 1 or matches[0]["sha256"] != digest(content):
            raise ValueError(f"분리 명세와 파일 해시가 다릅니다: {key}")
        frame = pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False)
        if not {"stock_code", "market", "date", "close"}.issubset(frame.columns):
            raise ValueError(f"필수 열이 없습니다: {key}")
        if not frame["stock_code"].eq("005930").all() or not frame["market"].eq("KRX").all():
            raise ValueError(f"종목 또는 시장이 다릅니다: {key}")
        if len(frame) != count or frame["date"].iloc[0] != start or frame["date"].iloc[-1] != end:
            raise ValueError(f"합의한 구간과 다릅니다: {key}")
        frames.append(frame)
        inputs[path] = content

    prices = pd.concat(frames, ignore_index=True)
    require_complete_dates(parse_dates(prices["date"]), expected_dates)
    before = prices.copy(deep=True)
    full = calculate_signals(prices)
    reference_path = ROOT / "data/stock-day40/005930_2025_signals.csv"
    reference = read_reference(reference_path, len(prices))
    if reference["date"].tolist() != prices["date"].tolist():
        raise ValueError("40일차 앞 183행과 현재 개발·검증 날짜가 다릅니다.")

    # CSV 저장·재읽기로 생길 수 있는 아주 작은 실수 표현 차이만 허용합니다.
    # 문자열 신호는 정확히 같아야 하며 결측 위치도 동일해야 합니다.
    for column in ("ma_5", "ma_20"):
        saved = pd.to_numeric(reference[column].replace("", float("nan")), errors="raise")
        pd.testing.assert_series_equal(
            full[column], saved, check_names=False, check_dtype=False,
            check_exact=False, rtol=1e-12, atol=1e-9,
        )
    for column in ("close_signal", "previous_signal"):
        if full[column].tolist() != reference[column].tolist():
            raise ValueError(f"40일차 신호와 재계산 결과가 다릅니다: {column}")

    # 입력을 처음부터 잘라 계산하므로 각 시점에 아직 없던 미래 행을 사용할 수 없습니다.
    # 처음 19행의 이동평균 준비 구간은 이후 검사에서도 그대로 유지합니다.
    cut_points = list(range(20, len(prices)))
    changed = find_changed_prefixes(prices, calculate_signals, cut_points)
    if changed:
        raise AssertionError(f"미래 행 추가 후 과거 결과가 달라졌습니다: {changed}")
    assert 118 in cut_points
    pd.testing.assert_frame_equal(prices, before)
    for path, content in inputs.items():
        if path.read_bytes() != content:
            raise ValueError(f"검사 중 입력 파일 변경이 발견되었습니다: {path}")
    pd.testing.assert_frame_equal(read_reference(reference_path, len(prices)), reference)

    summary = {
        "stock_code": "005930", "rows": len(prices),
        "first_date": prices["date"].iloc[0], "last_date": prices["date"].iloc[-1],
        "development_rows": 118, "validation_rows": 65,
        "cut_start": 20, "cut_end": len(prices) - 1, "cut_count": len(cut_points),
        "changed_cut_points": changed, "day40_reference_match": True,
        "development_boundary_match": True, "final_evaluation_csv_read": False,
        "input_sha256": {path.relative_to(ROOT).as_posix(): digest(content) for path, content in inputs.items()},
        "day40_prefix_sha256": digest(reference.to_csv(index=False, lineterminator="\n").encode("utf-8")),
        "calculator_sha256": digest((HERE / "check_prefix.py").read_bytes()),
    }
    report = f"""# 47일차 과거 신호 불변 검사 결과

- 대상: 삼성전자 005930, KRX.
- 입력: 개발 118행과 검증 65행, 총 {len(prices)}행.
- 기간: {summary['first_date']} ~ {summary['last_date']}.
- 40일차 앞 183행의 이동평균·마감 신호·전날 신호 대조: 통과.
- 비교 지점: 앞 20행부터 앞 182행까지 {len(cut_points)}개.
- 미래 행 추가 후 과거 결과 변화: 0개 지점.
- 개발 118행과 개발·검증 183행의 같은 과거 구간 비교: 통과.
- 초기 이동평균 결측 위치를 포함한 과거 결과 불변 검사: 통과.
- 입력 표·입력 파일 보존 검사: 통과.
- 최종 평가 CSV 읽기·실제 주문·인터넷 요청·수익률 계산: 없음.

## 검사 방법과 범위

입력을 각 시점까지 잘라 이동평균과 신호를 처음부터 다시 계산하고,
개발·검증 전체를 계산한 결과의 같은 과거 구간과 비교했다.
40일차 원본 프로그램은 실행하지 않았으며 교차·동률·초기 결측 규칙을 검증용 함수로 옮겼다.
저장된 40일차 파일에서는 날짜가 일치하는 앞 183행만 읽어 대조했다.
이동평균의 저장값 대조에는 작은 실수 표현 오차를 허용했고 신호는 정확히 비교했다.
입력 길이를 달리한 재계산 결과끼리는 결측 위치와 숫자·신호를 정확히 비교했다.

이번 통과는 이 입력 자료와 계산 함수에서 미래 행 추가에 따른 과거 결과 변화가
발견되지 않았다는 뜻이다. 전체 백테스트의 모든 정보 누출이 없다는 증명은 아니다.
체결·비용·성과 계산과 데이터 공급자의 과거 가격 수정 이력은 검사 대상이 아니다.
2025년 전체 성과를 이미 본 사실은 달라지지 않으며 최종 구간의 독립성을 새로 확보한 것도 아니다.
"""
    targets = {
        HERE / "prefix_report.md": report.encode("utf-8"),
        ROOT / "data/stock-day47/prefix_summary.json": (json.dumps(summary, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    }
    for path, content in targets.items():
        check_existing(path, content)
    for path, content in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        check_existing(path, content)
        if not path.exists():
            with path.open("xb") as handle:
                handle.write(content)
        if path.read_bytes() != content:
            raise ValueError(f"저장 결과가 다릅니다: {path}")

    print(f"입력: 개발 118행 + 검증 65행 = {len(prices)}행")
    print(f"기간: {summary['first_date']} ~ {summary['last_date']}")
    print("40일차 이동평균·마감 신호·전날 신호 대조: 통과")
    print(f"비교 지점: 앞 20행부터 182행까지 {len(cut_points)}개")
    print("미래 행 추가 후 과거 결과 변화: 0개 지점")
    print("개발 118행과 전체 183행의 과거 구간 비교: 통과")
    print("입력 표·파일 보존·결과 저장 검사: 통과")
    print("최종 평가 CSV 읽기·인터넷 요청·주문·수익률 계산: 없음")
    for path in targets:
        print(f"저장: {path}")


if __name__ == "__main__":
    main()
