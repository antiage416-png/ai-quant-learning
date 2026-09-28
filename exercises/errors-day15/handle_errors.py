from urllib.request import urlopen
from urllib.error import HTTPError, URLError

# 내 컴퓨터의 연습용 서버로 요청합니다.
url = "http://127.0.0.1:8765/"

try:
    # 요청을 시도합니다.
    # timeout은 네트워크 작업의 대기 시간을 제한합니다.
    with urlopen(url, timeout=1) as response:
        body = response.read()
        print("요청 성공:", response.status)
        print("받은 크기:", len(body), "바이트")

except HTTPError as error:
    # 서버가 HTTP 오류 상태를 반환한 경우 실행합니다.
    print("HTTP 오류가 발생했습니다.")
    print("상태 코드:", error.code)
    print("요청 주소:", error.url)
    error.close()

except URLError as error:
    # 연결 과정의 타임아웃이 URLError 안에 담겨 올 수도 있습니다.
    if isinstance(error.reason, TimeoutError):
        print("연결 대기 시간이 초과됐습니다.")
    else:
        print("연결 오류가 발생했습니다.")
        print("이유:", error.reason)

except TimeoutError:
    # 응답을 읽는 중 등에 직접 발생한 타임아웃을 처리합니다.
    print("네트워크 작업의 대기 시간이 초과됐습니다.")

print("요청 처리가 끝났습니다.")