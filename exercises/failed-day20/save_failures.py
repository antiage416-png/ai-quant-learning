import json
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

# 정상 주소와 실패 확인용 주소입니다.
urls = [
    "https://quotes.toscrape.com/",
    "https://quotes.toscrape.com/practice-missing-page-day15/",
]

# 실패한 요청의 정보를 모을 목록입니다.
failures = []

for url in urls:
    try:
        with urlopen(url, timeout=20) as response:
            response.read()
            print("성공:", response.status, url)

    except HTTPError as error:
        # 실패한 주소와 HTTP 상태 코드를 함께 기록합니다.
        failures.append({
            "url": url,
            "reason": f"HTTP {error.code}",
        })
        print("실패:", error.code, url)
        error.close()

    except (URLError, TimeoutError) as error:
        # 서버 연결이나 대기 시간 문제도 목록에 기록합니다.
        failures.append({
            "url": url,
            "reason": str(error),
        })
        print("연결 또는 대기 시간 오류:", url)

# 이번 실행의 실패 목록을 JSON 파일로 저장합니다.
output_path = Path(__file__).resolve().parent / "failed_urls.json"

output_path.write_text(
    json.dumps(failures, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("실패 건수:", len(failures))
print("저장 위치:", output_path)