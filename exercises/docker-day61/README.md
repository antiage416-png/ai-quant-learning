# 9주차 61일차 — 환경변수로 DB 위치 지정

실습 날짜: 2026-10-13. 기존 DB를 다른 컨테이너 경로에 연결하고 환경변수로 API에 위치를 전달했다.

## 변경과 역할

- /home/jaeho/ai-quant-learning/exercises/api-day56/price_store.py에 os.getenv로 PRICE_DB_PATH를 읽는 코드를 추가했다. 설정이 없으면 기존 data/stock-day56/prices.db 경로를 사용한다.
- 환경변수는 프로그램에 사용할 경로를 알려 준다. 파일을 복사하거나 연결하지 않는다. 모듈을 불러올 때 설정값을 읽는다.
- 마운트는 외부 폴더를 컨테이너에서 볼 수 있게 연결한다. 이번에는 이름 있는 Docker 볼륨이 아니라 기존 Ubuntu 폴더의 bind mount를 사용했다.
- DB 원본은 그대로 유지하며 읽기 전용으로 연결했다.

## 실행 기록

Ubuntu 터미널에서 실행했다. 호스트 가상환경 활성화는 Docker 명령에 필수가 아니다. -f는 Dockerfile 위치, -t는 이미지 이름·태그, 마지막 점은 빌드 입력 기준 폴더다. 빌드는 다운로드와 이미지 저장을 수반할 수 있다.

```bash
# 프로젝트 루트를 빌드 기준으로 사용합니다.
cd /home/jaeho/ai-quant-learning

# 수정된 DB 조회 코드를 포함한 이미지를 만듭니다.
docker build -f exercises/docker-day59/Dockerfile -t quant-api:day61 .
```

다음은 최초 컨테이너 생성 기록이다. 현재 같은 이름의 컨테이너가 남아 있으므로 그대로 반복 실행하지 않는다. -d는 백그라운드, -p는 로컬 8003과 컨테이너 8000 연결, -e는 환경변수 전달이다. readonly는 마운트의 쓰기를 금지한다.

```bash
# DB 폴더를 /storage에 연결하고 API가 읽을 파일 위치를 전달합니다.
docker run -d --name quant-api-day61 \
    -p 127.0.0.1:8003:8000 \
    --mount type=bind,source=/home/jaeho/ai-quant-learning/data/stock-day56,target=/storage,readonly \
    -e PRICE_DB_PATH=/storage/prices.db \
    quant-api:day61
```

- 환경변수는 컨테이너에서 보이는 /storage/prices.db를 지정한다.
- 환경변수만 지정하고 DB를 연결하지 않으면 이번 이미지에는 DB가 없으므로 읽을 수 없다. 해당 실패를 실제로 실행 검사한 것은 아니다.
- 브라우저 확인 주소: http://127.0.0.1:8003/api/price-change?stock_code=005930&start_date=2025-01-02&end_date=2025-01-06

## 실제 확인

- Python 문법 검사 및 별도 프로세스에서 환경변수 유무에 따른 경로 선택을 확인했다. 기본값과 /storage/prices.db가 각각 선택됐다. 이 검사는 경로 선택만 확인했다.
- quant-api:day61 빌드 성공. 변경 없는 패키지 설치 단계는 캐시를 사용했다.
- quant-api-day61 실행 상태와 127.0.0.1:8003 → 8000 연결을 확인했다.
- 브라우저 응답: 첫 종가 53400, 마지막 종가 55900, 종가 변화율 4.68164794007491%. 60일차와 같은 결과였다.
- Docker inspect에서 PRICE_DB_PATH=/storage/prices.db, bind 대상 /storage, RW=false를 확인했다.
- Docker Desktop Files에서 storage/prices.db가 보이는 것을 사용자 화면으로 확인했다.
- 사용자는 처음 환경변수만 있으면 조회할 수 있다고 답했다. 설명 후 외부 DB를 컨테이너에서 읽으려면 연결이 필요하다는 점을 자신의 말로 정리했다.

## 보관 상태와 다음 단계

마무리 때 quant-api-day61을 정상 중지했다(종료 코드 0). 이미지·컨테이너·원본 DB를 보관한다. 다시 실행할 때는 기존 컨테이너를 사용한다.

```bash
# 보관한 컨테이너를 기존 설정으로 다시 시작합니다.
docker start quant-api-day61

# 확인 후 서버를 중지합니다. 원본 DB는 유지됩니다.
docker stop quant-api-day61
```

다음 62일차에는 컨테이너 재생성 전후에 데이터가 유지되는지 확인한다. 이번에는 재생성·전체 오류 경로·독립적인 구현 숙련도까지 검증하지 않았다.
