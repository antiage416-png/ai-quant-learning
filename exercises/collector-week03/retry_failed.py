import json
import time
from pathlib import Path
from collect import collect_one, logger

current_dir = Path(__file__).resolve().parent
input_path = current_dir / "failed_urls.json"
output_path = current_dir / "remaining_failures.json"

# 최초 실패 목록을 읽습니다.
failures = json.loads(input_path.read_text(encoding="utf-8"))

remaining = []
success_count = 0

logger.info("실패 항목 재실행 시작: 대상=%d", len(failures))

for number, item in enumerate(failures, start=1):
    # 첫 요청은 바로 실행하고, 두 번째 항목부터는 2초 쉽니다.
    if number > 1:
        logger.info("다음 주소 요청 전 2초 대기")
        time.sleep(2)

    failure = collect_one(item["url"])

    if failure is None:
        # 성공한 항목은 남은 실패 목록에 넣지 않습니다.
        success_count += 1
    else:
        remaining.append(failure)

# 최초 목록은 유지하고, 이번 재실행 결과를 별도로 저장합니다.
output_path.write_text(
    json.dumps(remaining, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

logger.info(
    "재실행 종료: 성공=%d, 남은 실패=%d",
    success_count,
    len(remaining),
)

