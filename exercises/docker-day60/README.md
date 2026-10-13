# 9주차 60일차 — 분석 API 이미지 빌드와 실행

실습 날짜: 2026-10-13. 59일차 설명서로 이미지를 만들고 기존 DB를 연결해 API 응답을 확인했다.

## 구성과 실제 결과

- 이미지: quant-api:day60. 컨테이너: quant-api-day60 (ID 앞부분 abb31cca3f03).
- Dockerfile: /home/jaeho/ai-quant-learning/exercises/docker-day59/Dockerfile.
- 코드: /home/jaeho/ai-quant-learning/exercises/api-day56/main.py에 GET /health 추가. DB 상태를 검사하는 경로는 아니다.
- 브라우저 → 127.0.0.1:8002 → 컨테이너 8000 → API → 읽기 전용 DB → 계산 응답.
- DB 원본 디렉터리: /home/jaeho/ai-quant-learning/data/stock-day56. 연결 대상: /app/data/stock-day56.
- 연결 방식은 기존 호스트 폴더의 bind mount다. 58일차의 이름 있는 볼륨과 구분한다. Docker inspect에서 RW=false 확인.
- /health: {"status":"ok"}. 브라우저 응답과 로그의 HTTP 200 확인.
- /api/price-change?stock_code=005930&start_date=2025-01-02&end_date=2025-01-06: 첫 종가 53400, 마지막 종가 55900, 변화율 4.68164794007491%. HTTP 200 확인.
- 위 분석은 종가 변화율이며 비용 반영 백테스트 성과가 아니다. 모든 종목·오류 경로까지 검사한 것은 아니다.

## 실행 방법 기록

아래는 Ubuntu 터미널용이다. 호스트 가상환경 활성화는 필수가 아니다. 빌드에는 인터넷 다운로드와 디스크 저장이 발생한다. -f는 설명서 위치, -t는 이미지 이름·태그, 마지막 점은 프로젝트 전체를 빌드 입력 기준으로 지정한다.

```bash
# 프로젝트 루트를 빌드 입력의 기준으로 삼습니다.
cd /home/jaeho/ai-quant-learning

# Dockerfile대로 패키지 설치와 코드 복사를 수행해 이미지를 만듭니다.
docker build -f exercises/docker-day59/Dockerfile -t quant-api:day60 .
```

다음은 최초 생성 기록이다. 현재 같은 이름의 컨테이너가 남아 있으므로 그대로 반복 실행하지 않는다. -d는 백그라운드 실행, -p는 로컬 포트 연결, readonly는 DB 폴더 읽기 전용 연결이다.

```bash
# 최초 실습에서 컨테이너를 생성하고 포트와 DB 폴더를 연결했습니다.
docker run -d --name quant-api-day60 \
    -p 127.0.0.1:8002:8000 \
    --mount type=bind,source=/home/jaeho/ai-quant-learning/data/stock-day56,target=/app/data/stock-day56,readonly \
    quant-api:day60
```

기존 컨테이너를 다시 켤 때는 아래 start를 사용한다. 이미지 재빌드는 기존 컨테이너의 코드를 교체하지 않으므로 코드 변경을 반영하려면 이후 컨테이너 재생성 과정을 별도로 진행한다.

```bash
# 보관한 기존 컨테이너를 다시 시작합니다.
docker start quant-api-day60

# 서버의 실행 기록을 최근 20줄만 읽습니다.
docker logs --tail 20 quant-api-day60

# 확인을 마친 서버를 중지합니다. 이미지와 DB는 남습니다.
docker stop quant-api-day60
```

서버 실행 후 브라우저에서 http://127.0.0.1:8002/health 와 위 분석 경로를 확인한다. 마무리 시 컨테이너는 중지했으며 이미지·원본 DB는 유지했다.

## Docker Desktop에서 확인한 것

- Logs: 서버 시작과 GET 요청의 200 응답. favicon.ico의 404는 아이콘 미제공 기록이다.
- Bind mounts: Ubuntu DB 원본 폴더 표시.
- Files: /app 아래 data·exercises·requirements.txt 표시. 실행 중 보이는 DB는 연결된 파일이며 이미지에 복사한 것이 아니다.
- Desktop과 Ubuntu 명령은 같은 Docker Desktop 엔진의 컨테이너를 다룬다.

다음 61일차에는 환경변수와 볼륨을 전달해 데이터 저장 위치를 분리한다. 기존 읽기 전용 연결과 새로 작성할 내용을 구분해 작은 단계로 진행한다.
