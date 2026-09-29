import json
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

current_dir = Path(__file__).resolve().parent
input_path = current_dir / "failed_urls.json"

# JSON 파일의 내용을 Python 목록으로 복원합니다.
failures = json.loads(input_path.read_text(encoding="utf-8"))

remaining = []
success_count = 0

print("재실행 대상:", len(failures))

for item in failures:
    # 이전에 실패한 항목에서 주소만 꺼냅니다.
    url = item["url"]
    print("재요청:", url)

    try:
        with urlopen(url, timeout=20) as response:
            response.read()
            print("성공:", response.status)

        success_count += 1

    except HTTPError as error:
        remaining.append({
            "url": url,
            "reason": f"HTTP {error.code}",
        })
        print("다시 실패:", error.code)
        error.close()

    except (URLError, TimeoutError) as error:
        remaining.append({
            "url": url,
            "reason": str(error),
        })
        print("연결 또는 대기 시간 오류:", error)

# 최초 실패 목록은 유지하고, 이번 결과를 별도 파일에 저장합니다.
output_path = current_dir / "remaining_failures.json"
output_path.write_text(
    json.dumps(remaining, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("재실행 성공:", success_count)
print("남은 실패:", len(remaining))