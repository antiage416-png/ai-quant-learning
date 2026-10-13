# 9주차 62일차 — 컨테이너 재생성 후 DB 보존 확인

실습 날짜: 2026-10-13. 61일차 컨테이너를 삭제하고 같은 이미지·설정으로 다시 만들어 외부 DB 보존을 확인했다.

## 비교 결과

| 항목 | 재생성 전 | 재생성 후 |
| --- | --- | --- |
| 컨테이너 이름 | quant-api-day61 | quant-api-day61 |
| 컨테이너 ID 앞부분 | be96a8e91cf0 | 383256deab16 |
| 이미지 태그 | quant-api:day61 | quant-api:day61 |
| DB 행 수 | 000660·005930 각각 118행 | 각각 118행 |
| 종가 변화율 | 4.68164794007491% | 4.68164794007491% |

동일 이미지 ID: sha256:ae9fb0ab8edb6c4d2ce221ec190fa780bddd112125e91f1c8218bbb06f492e8b.

DB SHA256은 전후 모두 6a635ec0dc777a22612edae0c916fcbd9bb0d02f06b9e1580212fd3ba2018505였다. 원본 파일 내용이 유지됐음을 확인했다.

## 유지한 연결

- 원본 DB: /home/jaeho/ai-quant-learning/data/stock-day56/prices.db
- 컨테이너 연결 폴더: /storage
- 환경변수: PRICE_DB_PATH=/storage/prices.db
- 방식: 기존 Ubuntu 폴더를 읽기 전용 bind mount로 연결. 이름 있는 Docker 볼륨 실습과 구분한다.
- 포트: 127.0.0.1:8003 → 컨테이너 8000

## 실행 기록

Ubuntu 터미널에서 실행했다. Docker 명령에는 호스트 Python 가상환경 활성화가 필수가 아니다. 아래 삭제·생성 명령은 완료한 실습 기록이며 무작정 재실행하지 않는다. rm은 지정한 중지 컨테이너를 삭제하고, 연결된 원본 DB와 이미지는 보관한다.

```bash
# 재생성 전 컨테이너 ID와 중지 상태를 조회했습니다.
docker ps -a --filter 'name=^/quant-api-day61$'

# 기존 중지 컨테이너만 삭제했습니다.
docker rm quant-api-day61

# 같은 이미지로 새 컨테이너를 만들고 원본 DB를 다시 연결했습니다.
docker run -d --name quant-api-day61 \
    -p 127.0.0.1:8003:8000 \
    --mount type=bind,source=/home/jaeho/ai-quant-learning/data/stock-day56,target=/storage,readonly \
    -e PRICE_DB_PATH=/storage/prices.db \
    quant-api:day61

# 새 ID와 실행 상태를 확인했습니다.
docker ps -a --filter 'name=^/quant-api-day61$'
```

-d는 백그라운드 실행, -p는 포트 연결, --mount는 기존 DB 폴더 연결, readonly는 쓰기 금지, -e는 DB 경로 설정 전달이다. 이미지 빌드는 다시 하지 않았다.

브라우저에서 다음 주소를 요청해 첫 종가 53400·마지막 종가 55900·변화율 4.68164794007491% 응답을 확인했다.

http://127.0.0.1:8003/api/price-change?stock_code=005930&start_date=2025-01-02&end_date=2025-01-06

도우미가 읽기 전용 DB 조회로 종목별 행 수를 비교하고, 파일 해시와 이미지 ID·마운트 설정을 확인했다. 다른 컴퓨터 재현과 모든 오류 경로까지 검증한 것은 아니다.

## 이해 확인과 마무리

사용자는 DB가 외부에 있기 때문에 컨테이너 삭제 후에도 남는다고 설명했다. 같은 이름이어도 새 ID를 가진 별도 컨테이너이며, 외부 원본을 다시 연결해 읽는 구조다.

재생성한 컨테이너는 실습 후 정상 중지했고 종료 코드는 0이었다. 이미지·새 컨테이너·원본 DB를 보관한다.

```bash
# 보관 중인 새 컨테이너를 기존 설정으로 다시 시작할 때 사용합니다.
docker start quant-api-day61

# 확인을 마친 서버를 중지할 때 사용합니다.
docker stop quant-api-day61
```

다음 63일차에는 빌드·실행·로그·중지 절차를 정리하고 다른 컴퓨터에서 가능한 범위까지 재현한다. 다른 컴퓨터의 환경과 데이터 유무부터 확인한다.
