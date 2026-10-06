## 51일차 — FastAPI 상태 확인 API

### 목표와 구조

FastAPI로 요청 주소와 Python 함수를 연결하고,
Uvicorn으로 서버를 실행해 실제 JSON 응답을 확인한다.

GET /api/health 요청
→ health_check() 실행
→ {"status": "ok"} 반환
→ JSON 응답

FastAPI는 요청 경로와 처리 함수를 정의하고,
Uvicorn은 앱을 서버로 실행해 요청을 받는다.

### 환경

- Ubuntu의 기존 가상환경:
  /home/jaeho/ai-quant-learning/.venv
- FastAPI: 0.142.2
- Uvicorn: 0.54.0
- 두 패키지의 import와 버전 출력을 확인했다.
- python -m pip check 결과: No broken requirements found.

### 코드 작성 과정

- 빈 main.py에 작은 코드 블록을 직접 추가했다.
- FastAPI 객체를 만들고 app 변수에 저장했다.
- @app.get("/api/health")로 GET 요청과 함수를 연결했다.
- 함수에서 상태 확인용 딕셔너리를 반환했다.

main.py를 Python으로 직접 실행하면 앱 생성과 경로 등록 후 종료된다.
요청을 계속 받으려면 Uvicorn으로 실행해야 한다.

### 실행 방법

Ubuntu 터미널에서 다음 명령으로 실행한다.

```bash
# main.py의 app 객체를 기존 가상환경의 Uvicorn으로 실행합니다.
# --app-dir는 모듈 위치, --host는 로컬 주소, --port는 요청을 받을 포트입니다.
/home/jaeho/ai-quant-learning/.venv/bin/python -m uvicorn main:app \
    --app-dir /home/jaeho/ai-quant-learning/exercises/api-day51 \
    --host 127.0.0.1 \
    --port 8000
```

main:app은 main.py 안의 app 객체를 의미한다.
서버 실행 중에는 터미널이 요청을 기다리며 입력 줄로 돌아오지 않는다.

### 확인 주소와 실제 결과

- 상태 확인: http://127.0.0.1:8000/api/health
- 자동 문서: http://127.0.0.1:8000/docs

브라우저에서 상태 확인 주소를 열어 {"status":"ok"}를 확인했다.

자동 문서에서 GET /api/health를 펼치고,
Try it out → Execute로 요청했다.

- 상태 코드: 200
- 응답 본문: {"status":"ok"}
- 응답 형식: application/json

상태 확인 함수는 정해진 응답을 반환한다.
가격 자료·데이터베이스·백테스트 전체의 정상 여부를 검사하는 기능은 아니다.

### 오류와 해결

- 처음 / 경로를 열었을 때 404와 {"detail":"Not Found"}가 나왔다.
- 등록한 /api/health 경로로 요청해 정상 응답을 확인했다.
- 예상 출력문을 터미널 명령으로 입력한 과정에서 셸 안내가 나타났다.
- 올바른 Uvicorn 실행 명령으로 서버를 시작해 정상 동작을 확인했다.
- 실행할 명령과 예상 출력 예시를 구분한다.

### 종료

서버를 실행한 터미널에서 Ctrl+C를 눌러 종료한다.

실제로 Application shutdown complete와 Finished server process를 확인했고,
터미널 입력 줄로 돌아왔다. 작성한 코드 파일은 유지된다.

### 범위와 다음 단계

- 앱 생성·경로 등록·서버 실행·브라우저 호출·자동 문서 호출·종료를 확인했다.
- 외부 가격 조회·실제 주문·백테스트 계산은 수행하지 않았다.
- 실행 성공과 독립적인 구현 숙련도는 구분한다.
- 다음은 52일차: 종목·기간 입력 검증과 일봉 조회 API 구현이다.