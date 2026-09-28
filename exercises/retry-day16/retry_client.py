import time
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

url = "http://127.0.0.1:8766/"
max_attempts = 3  # 첫 요청을 포함해 최대 3번 시도합니다.

for attempt in range(1, max_attempts + 1):
    print(f"{attempt}번째 요청")

    try:
        with urlopen(url, timeout=5) as response:
            body = response.read().decode("utf-8")
            print("성공:", response.status)
            print("본문:", body)

        # 성공하면 반복을 끝냅니다.
        break

    except HTTPError as error:
        status = error.code
        retry_after = error.headers.get("Retry-After")
        error.close()

        print("HTTP 오류:", status)

        # 이번 실습에서는 429만 재시도합니다.
        if status != 429:
            print("재시도 대상이 아니므로 종료합니다.")
            break

        if attempt == max_attempts:
            print("최대 시도 횟수에 도달했습니다.")
            break

        # 이번 연습 서버가 보내는 초 단위 값을 처리합니다.
        # 날짜 형식이나 값이 없는 경우는 아직 처리하지 않습니다.
        if retry_after is None or not retry_after.strip().isdigit():
            print("초 단위 Retry-After가 없어 종료합니다.")
            break

        wait_seconds = int(retry_after.strip())
        print(f"{wait_seconds}초 기다린 뒤 다시 요청합니다.")
        time.sleep(wait_seconds)

    except (URLError, TimeoutError) as error:
        print("연결 또는 대기 시간 오류:", error)
        print("이번 실습에서는 이 오류를 재시도하지 않습니다.")
        break

print("요청 처리가 끝났습니다.")