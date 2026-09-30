# 목적:
# 11월까지 완료된 상태에서 12월만 추가하고,
# 다시 실행하면 요청하지 않는지 검사합니다.
#
# 흐름:
# 임시 상태 준비 → API 함수를 연습용으로 대체
# → 기존 수집 코드 실행 → 요청 기간·상태 갱신 검사 → 재실행
#
# 실행 영향:
# 인터넷 요청과 실제 인증정보 읽기는 없습니다.
# 실제 data/stock-day33과 CSV는 변경하지 않습니다.
# 임시 폴더만 사용하며 검사가 끝나면 자동으로 정리됩니다.

import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

# import만으로 main()은 실행되지 않습니다.
import collect_incremental as collector


def main():
    """별도 임시 상태에서 기존 증분 수집 로직을 검사합니다."""

    # 테스트가 끝나면 임시 폴더와 그 안의 파일을 자동 정리합니다.
    with TemporaryDirectory(prefix="stock-day33-check-") as directory:
        temporary_dir = Path(directory)
        state_path = temporary_dir / "state.json"

        # 삼성전자 한 종목이 11월까지 완료됐다고 가정합니다.
        # 이는 검사 전용 가정이며 실제 수집 기록을 바꾸지 않습니다.
        initial_state = {
            "conditions": collector.CONDITIONS,
            "stocks": {
                "005930": {
                    "covered_through": "2025-11-30",
                    "batches": [],
                }
            },
        }
        state_path.write_text(
            json.dumps(initial_state),
            encoding="utf-8",
        )

        def fake_fetch(code, start, end, token):
            """요청 대신 임시 파일을 만들고 저장 결과 형식만 반환합니다."""

            # 이 파일은 시세가 아니라 파일 연결 확인용 연습 자료입니다.
            # 가격 품질 검사는 앞서 실제 CSV로 수행했습니다.
            raw_name = "sample_raw.json"
            meta_name = "sample_meta.json"
            for filename in [raw_name, meta_name]:
                (temporary_dir / filename).write_text(
                    '{"practice": true}',
                    encoding="utf-8",
                )

            return {
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "count": 1,
                "raw_file": raw_name,
                "meta_file": meta_name,
            }

        # with 블록 안에서만 설정과 함수를 교체합니다.
        # 블록을 벗어나면 원래 설정으로 돌아옵니다.
        with (
            patch.object(collector, "DATA_DIR", temporary_dir),
            patch.object(collector, "STATE_PATH", state_path),
            patch.object(collector, "STOCKS", {"005930": "삼성전자"}),
            patch.object(collector, "END_DATE", date(2025, 12, 31)),
            patch.object(
                collector, "get_access_token", return_value="practice-token"
            ) as auth,
            patch.object(
                collector, "fetch_month", side_effect=fake_fetch
            ) as fetch,
        ):
            print("[첫 실행: 11월 완료 상태]")
            collector.main()

            # 월별 요청 함수가 정확히 12월 범위로 한 번 호출됐는지 검사합니다.
            fetch.assert_called_once_with(
                "005930",
                date(2025, 12, 1),
                date(2025, 12, 31),
                "practice-token",
            )

            saved = json.loads(state_path.read_text(encoding="utf-8"))
            if saved["stocks"]["005930"]["covered_through"] != "2025-12-31":
                raise ValueError("완료 날짜가 갱신되지 않았습니다.")

            print("\n[두 번째 실행: 12월 완료 상태]")
            collector.main()

            # 두 번 실행한 후에도 총 호출 횟수가 1이면
            # 두 번째 실행에서는 추가 요청·인증이 없었다는 뜻입니다.
            if fetch.call_count != 1 or auth.call_count != 1:
                raise ValueError("완료 후 불필요한 호출이 발생했습니다.")

        print("\n다음 미수집 기간 계산: 통과")
        print("저장 후 완료 날짜 갱신: 통과")
        print("재실행 시 추가 호출 없음: 통과")
        print("실제 API 요청: 0회")
        print("실제 수집 상태·CSV 변경: 없음")


if __name__ == "__main__":
    main()