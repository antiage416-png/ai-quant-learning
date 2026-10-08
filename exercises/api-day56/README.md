# 8주차 56일차 — 주가 DB와 분석 API 연결

## 목표와 현재 흐름

기존 수집 CSV → 개발 기간 자료를 SQLite에 저장 →
종목·기간별 DB 조회 → 기존 변화율 계산 → JSON 응답.

외부 수집기가 DB를 직접 갱신하는 구조는 아니다.
CSV에서 DB로 옮기는 프로그램을 별도로 실행한다.

## 구성

- build_price_db.py: CSV 검사, 테이블 생성, 추가·갱신, 재조회 대조.
- price_store.py: 읽기 전용 DB 조회 함수.
- main.py: DB 기반 종가 변화율 API.
- check_api.py: CSV·DB 기반 API의 두 종목 응답 대조.
- DB: /home/jaeho/ai-quant-learning/data/stock-day56/prices.db
- 원본: /home/jaeho/ai-quant-learning/data/stock-day33/clean/

## 저장 범위와 규칙

- 삼성전자 005930, SK하이닉스 000660.
- 기간: 2025-01-02~2025-06-30.
- 종목별 118행, 합계 236행.
- 기본키: stock_code와 date의 조합.
- 같은 기본키는 갱신하고 새로운 기본키는 추가한다.
- 재실행 시 원본에서 삭제된 행을 DB에서도 삭제하는 기능은 없다.
- DB 조회는 읽기 전용이며 날짜순으로 반환한다.
- 원본 CSV는 변경하지 않는다.

## 검증 결과

- 최초 저장과 재실행 모두 DB 236행 유지.
- DB 재조회 결과와 CSV 준비 자료의 전체 값 대조 통과.
- 삼성전자 1월 2일·3일·6일의 날짜와 종가 조회 검사 통과.
- 두 종목의 CSV·DB API 응답 대조 통과.
- 삼성전자 개발 기간 종가 변화율 약 11.9850%.
- SK하이닉스 개발 기간 종가 변화율 약 70.5607%.
- DB API에 7월까지 요청하면 기간 안내와 HTTP 400 반환.
- 기존 CSV API에 거래일 하루를 요청하면 거래일 부족 설명과 HTTP 400 반환.

## 실행 방법

Ubuntu에서 기존 가상환경의 파이썬을 사용한다.
DB를 준비하는 명령은 자료를 추가·갱신한다.

```bash
# CSV 자료를 DB에 저장하고 재조회 결과를 대조합니다.
/home/jaeho/ai-quant-learning/.venv/bin/python \
    /home/jaeho/ai-quant-learning/exercises/api-day56/build_price_db.py
```

비교할 때는 터미널 세 개를 사용한다.
첫 번째 터미널은 CSV 서버, 두 번째는 DB 서버를 실행한 채 유지한다.
세 번째 터미널에서 비교 코드를 실행한다.

```bash
# 첫 번째 터미널: CSV 기반 서버를 실행합니다.
/home/jaeho/ai-quant-learning/.venv/bin/python -m uvicorn main:app \
    --app-dir /home/jaeho/ai-quant-learning/exercises/api-day52 \
    --host 127.0.0.1 \
    --port 8000
```

```bash
# 두 번째 터미널: DB 기반 서버를 실행합니다.
/home/jaeho/ai-quant-learning/.venv/bin/python -m uvicorn main:app \
    --app-dir /home/jaeho/ai-quant-learning/exercises/api-day56 \
    --host 127.0.0.1 \
    --port 8001
```

--app-dir은 코드 폴더, --host는 로컬 수신 주소,
--port는 서버별 포트 번호를 지정한다.

```bash
# 세 번째 터미널: 두 종목의 API 응답을 비교합니다.
/home/jaeho/ai-quant-learning/.venv/bin/python \
    /home/jaeho/ai-quant-learning/exercises/api-day56/check_api.py
```

검사를 마치면 각 서버 터미널에서 Ctrl+C로 종료한다.

## 오류와 해결

- 삽입 코드가 저장된 파일에 없어 DB가 0행으로 남았다.
  실제 파일 내용을 확인하고 삽입 코드를 추가·저장해 해결했다.
- 비교 시 CSV 서버의 8000번 포트에서 연결 거부가 발생했다.
  두 서버를 각각 실행하고 별도 터미널에서 비교해 해결했다.

## 해석과 남은 보완

- 두 API는 같은 계산 함수를 사용한다.
  응답 대조는 저장소 변경 후 동작 유지 검사이며 독립적인 계산식 검증은 아니다.
- 원본 시세 자체의 정확성까지 보장하지 않는다.
- 종가 변화율은 비용 반영 전략 수익률과 다르다.
- 외부 수집부터 DB 갱신까지의 자동 연결은 남아 있다.
- DB 누락·손상·잘못된 종가 등 모든 오류 경로를 실행 검증한 것은 아니다.
- 기존 거래일 기준과 계산 함수를 52일차 모듈에서 불러온다.
  공통 기능을 별도 모듈로 정리하는 작업은 남아 있다.
- 미체결 처리 예제의 전체 백테스트 통합과 구간별 계좌 성과 계산은 남아 있다.
- 이번 점검에서 과거 모든 실습을 재실행한 것은 아니다.