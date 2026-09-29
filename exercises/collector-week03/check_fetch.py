from collect import collect_one

# 세 번 모두 429가 오면 실패 정보가 반환되어야 합니다.
failure = collect_one("http://127.0.0.1:8766/")

if failure is None:
    print("결과: 성공")
else:
    print("결과: 실패")
    print("실패 주소:", failure["url"])
    print("실패 이유:", failure["reason"])