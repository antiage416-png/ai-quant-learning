# 9주차 63일차 — 분석 API 실행 안내서

2026-10-13 작성. PC 1에서 60~62일차에 확인한 절차를 통합했다. 이번 문서 작성 중 전체 빌드·실행을 반복하지 않았다. 사용자 요청으로 PC 2 재현은 보류이며 63일차 전체 완료로 처리하지 않는다.

## 실행 환경과 파일

아래 명령은 PC 1의 Ubuntu 터미널에서 사용한다. Docker Desktop을 켜고 Ubuntu WSL integration을 활성화한다. Docker 명령에는 호스트 Python 가상환경 활성화가 필수가 아니다.

- 저장소: /home/jaeho/ai-quant-learning
- Dockerfile: /home/jaeho/ai-quant-learning/exercises/docker-day59/Dockerfile
- 패키지 목록: 같은 폴더의 requirements.txt
- 제외 규칙: /home/jaeho/ai-quant-learning/.dockerignore
- API 코드: exercises/api-day56/main.py·price_store.py와 의존 코드 exercises/api-day52/main.py
- 외부 DB: /home/jaeho/ai-quant-learning/data/stock-day56/prices.db
- 이미지: quant-api:day61 / 컨테이너: quant-api-day61
- 접속: 127.0.0.1:8003 → 컨테이너 8000
- DB 연결: Ubuntu의 stock-day56 폴더 → /storage, 읽기 전용 bind mount
- 환경변수: PRICE_DB_PATH=/storage/prices.db

## 1. 읽기 전용 사전 확인

```bash
# 프로젝트를 빌드 입력 기준 폴더로 선택합니다.
cd /home/jaeho/ai-quant-learning

# 연결된 Docker 엔진을 확인합니다.
docker info --format '엔진 이름: {{.Name}} / 운영체제: {{.OperatingSystem}}'

# 기존 컨테이너 유무와 중지 상태를 확인합니다.
docker ps -a --filter 'name=^/quant-api-day61$'

# Docker에서 사용 중인 포트를 확인합니다.
docker ps --format '이름: {{.Names}} / 포트: {{.Ports}}'

# Ubuntu에서 8003번 포트의 대기 프로그램을 확인합니다.
ss -ltn 'sport = :8003'

# DB 파일 존재를 확인합니다. 없으면 실행 전에 자료를 준비합니다.
ls -l /home/jaeho/ai-quant-learning/data/stock-day56/prices.db
```

현재 PC 1에는 62일차에 재생성한 컨테이너가 중지 상태로 보관돼 있다. ID 앞부분은 383256deab16이다. 기존 컨테이너가 있으면 아래 첫 생성 절차 대신 4절을 사용한다. 포트 충돌이 있으면 사용 중인 프로그램을 임의 종료하지 말고 접속 포트를 따로 정한다. Ubuntu의 포트 조회만으로 Windows 전체 포트 사용을 확인한 것은 아니다.

## 2. 이미지를 처음 만들거나 코드 변경 반영하기

빌드는 필요한 다운로드와 디스크 저장을 수반한다. -f는 설명서 위치, -t는 이미지 이름·태그, 마지막 점은 현재 프로젝트를 입력 기준으로 삼는다.

```bash
# 프로젝트 루트로 이동합니다.
cd /home/jaeho/ai-quant-learning

# 현재 코드를 포함한 이미지를 만듭니다.
docker build -f exercises/docker-day59/Dockerfile -t quant-api:day61 .
```

기존 이미지를 다시 빌드해도 기존 컨테이너 안의 코드는 바뀌지 않는다. 변경한 코드를 적용하려면 새 컨테이너가 필요하다. 기존 컨테이너 제거는 보관 데이터와 대상 이름을 확인한 뒤 별도 단계로 진행한다.

## 3. 컨테이너 최초 생성 — 같은 이름이 없을 때만

-d는 백그라운드 실행, -p는 로컬 접속 포트 연결, --mount는 기존 폴더 연결, readonly는 쓰기 금지, -e는 프로그램에 DB 위치를 알려 주는 설정이다. 원본 DB를 이미지에 복사하지 않는다.

```bash
# 새 API 컨테이너를 만들고 외부 DB를 연결합니다.
docker run -d --name quant-api-day61 \
    -p 127.0.0.1:8003:8000 \
    --mount type=bind,source=/home/jaeho/ai-quant-learning/data/stock-day56,target=/storage,readonly \
    -e PRICE_DB_PATH=/storage/prices.db \
    quant-api:day61

# 실행 직후 상태를 확인합니다. 종료된 경우도 표시합니다.
docker ps -a --filter 'name=^/quant-api-day61$'
```

## 4. 기존 컨테이너 다시 시작

현재 PC 1에서는 보관된 컨테이너를 아래 명령으로 시작하면 된다. 이미지 빌드나 run을 반복할 필요가 없다.

```bash
# 기존 컨테이너를 저장된 환경변수·마운트·포트 설정으로 시작합니다.
docker start quant-api-day61
```

## 5. 응답과 로그 조회

조회 요청은 DB를 수정하지 않는다. -sS는 진행 표시를 숨기고 오류를 보여 주며, -w는 응답 뒤에 HTTP 코드를 표시한다. --max-time 10은 요청 대기 시간을 10초로 제한한다.

```bash
# API 서버의 응답 여부를 확인합니다. DB 연결까지 검사하는 경로는 아닙니다.
curl -sS --max-time 10 -w '\nHTTP 상태 코드: %{http_code}\n' http://127.0.0.1:8003/health

# 외부 DB 조회와 종가 변화율 계산을 확인합니다.
curl -sS --max-time 10 -w '\nHTTP 상태 코드: %{http_code}\n' 'http://127.0.0.1:8003/api/price-change?stock_code=005930&start_date=2025-01-02&end_date=2025-01-06'

# 최근 30줄의 서버 로그를 읽습니다.
docker logs --tail 30 quant-api-day61
```

예상값은 /health의 {"status":"ok"}, 분석의 첫 종가 53400·마지막 종가 55900·변화율 약 4.68164794007491%와 HTTP 200이다. 이 정상 응답은 60~62일차 실습에서 확인했으며 위 통합 명령 묶음을 이번에 새로 실행한 것은 아니다.

Desktop의 Containers에서 quant-api-day61을 선택하면 Logs로 요청 기록, Bind mounts로 외부 폴더 연결, Files의 /storage/prices.db로 연결된 파일을 볼 수 있다. favicon.ico의 404는 아이콘 미제공이며 분석 오류와 구분한다.

## 6. 종료

```bash
# 서버를 중지합니다. 컨테이너·이미지·원본 DB는 보관합니다.
docker stop quant-api-day61

# 종료 상태를 읽기 전용으로 확인합니다.
docker ps -a --filter 'name=^/quant-api-day61$'
```

## 문제를 만났을 때

| 증상 | 먼저 확인할 내용 |
| --- | --- |
| Docker WSL 통합 안내 | Desktop 실행과 Ubuntu integration |
| 컨테이너 이름 충돌 | 기존 컨테이너가 있는지 확인하고 재사용 또는 재생성 판단 |
| 포트 충돌 | 기존 서버와 Docker 포트 목록 확인 |
| 컨테이너가 바로 종료 | docker logs에서 오류 확인 |
| /health는 성공하지만 분석은 503 | 실제 DB 파일·PRICE_DB_PATH·마운트 경로 및 데이터 상태 확인 |
| 코드를 고쳤는데 응답이 그대로 | 새 이미지 빌드와 새 컨테이너 생성 여부 확인 |

## PC 2 재현 — 사용자 요청으로 보류

PC 2에서 실행 성공을 확인한 것은 아니다. 이전 환경 기록의 Windows Anaconda와 Docker 실행 환경은 별개다. 다음 재현 때 다음 사항부터 확인한다.

1. 실제 OS·WSL·Docker 지원 및 설치 상태, 디스크 여유 공간과 Git 작업 상태를 확인한다.
2. 최신 코드를 동기화하고 PC 2의 실제 저장소 절대경로를 확인한다. PC 1의 /home/jaeho 경로를 그대로 가정하지 않는다.
3. DB는 Git에서 제외되므로 코드만 받아서는 준비되지 않는다. 원본을 보존하면서 검증된 DB 사본을 별도로 준비하거나 필요한 원본 CSV를 준비해 생성한다. 이번에는 전송·생성을 수행하지 않았다.
4. PC 2의 실제 DB 원본 폴더를 --mount의 source에 지정한다. 컨테이너의 target=/storage와 PRICE_DB_PATH=/storage/prices.db는 일치시킨다.
5. 이름·포트를 확인하고 빌드·실행·응답·로그·중지를 단계별로 검증한다. 패키지 버전은 직접 의존성만 지정했고 Python 이미지 태그와 간접 의존성은 완전 고정하지 않았으므로 완전히 동일한 빌드를 보장하지 않는다.
6. 실제 확인한 결과만 환경 문서·일지·handoff에 추가한다.

현재 완료 범위는 실행 안내서 작성이다. PC 2 재현은 미완료로 유지한다.
