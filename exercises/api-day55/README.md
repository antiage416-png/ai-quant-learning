# 8주차 55일차 — 두 종목 분석 API와 저장 결과 대조

## 목적과 흐름

두 종목의 같은 기간 종가 변화율을 API로 조회하고,
응답을 JSON으로 저장한 뒤 원본 CSV의 직접 계산과 대조한다.

파이썬 요청 → 서버가 내부 CSV로 계산 → JSON 응답 →
클라이언트 파일 저장 → 다시 읽기 → 원본 CSV와 대조.

## 코드와 자료

- 서버: /home/jaeho/ai-quant-learning/exercises/api-day52/main.py
- 클라이언트: /home/jaeho/ai-quant-learning/exercises/api-day55/check_analysis.py
- 원본 폴더: /home/jaeho/ai-quant-learning/data/stock-day33/clean/
- 저장 폴더: /home/jaeho/ai-quant-learning/data/stock-day55/
- API: GET /api/price-change
- 입력: stock_code, start_date, end_date
- 결과 파일: price_change_{새 UUID}.json
- JSON 저장은 클라이언트가 수행하며 기존 결과를 덮어쓰지 않는다.

## 확인한 결과

조회 기간: 2025-01-02~2025-06-30.

| 종목 | 첫 종가 | 마지막 종가 | 종가 변화율 |
|---|---:|---:|---:|
| 삼성전자 005930 | 53,400 | 59,800 | 약 11.9850% |
| SK하이닉스 000660 | 171,200 | 292,000 | 약 70.5607% |

계산식: (마지막 종가 / 첫 종가 - 1) × 100.

- 브라우저와 파이썬 클라이언트의 조회 결과를 확인했다.
- 두 종목 응답의 JSON 저장·재읽기 비교가 통과했다.
- 원본 CSV를 직접 읽어 같은 기간을 선택하고 날짜순으로 정렬했다.
- 첫·마지막 거래일과 종가, 변화율과 백분율 대조가 통과했다.
- 직접 계산에는 API 계산 함수를 호출하지 않았다.
- 소수 계산 비교에는 isclose를 사용했다.

## 실행 방법

Ubuntu 첫 번째 터미널에서 서버를 실행하고 유지한다.

```bash
# 가격 조회·종가 변화율 서버를 로컬 8000번 포트에서 실행합니다.
/home/jaeho/ai-quant-learning/.venv/bin/python -m uvicorn main:app \
    --app-dir /home/jaeho/ai-quant-learning/exercises/api-day52 \
    --host 127.0.0.1 \
    --port 8000
```

--app-dir은 main.py 위치, --host는 수신 주소,
--port는 사용할 포트를 지정한다.

다른 Ubuntu 터미널에서 클라이언트를 실행한다.
실행할 때마다 새 JSON 파일이 생성된다.

```bash
# 두 종목 조회·저장·재읽기·원본 대조를 실행합니다.
/home/jaeho/ai-quant-learning/.venv/bin/python \
    /home/jaeho/ai-quant-learning/exercises/api-day55/check_analysis.py
```

53일차 서버와 같은 8000번 포트를 동시에 사용하지 않는다.
실습을 마치면 서버 터미널에서 Ctrl+C로 종료한다.

## 발생한 문제

클라이언트 실행 시 Connection refused가 발생했다.
서버를 실행한 뒤 다른 터미널에서 다시 요청해 정상 응답을 확인했다.

## 해석과 한계

- 저장 전후 비교는 저장 과정에서 내용이 바뀌지 않았는지 확인한다.
- 원본 직접 계산과 대조는 같은 원본을 기준으로 계산·응답을 확인한다.
- 원본 시세 자체의 정확성을 독립적으로 검증한 것은 아니다.
- 종가 변화율이며 수수료·세금·슬리피지를 반영한 전략 수익률이 아니다.
- 기존 백테스트의 비용·수량·체결 조건은 변경하지 않았다.
- 원본 CSV 수정·외부 시세 수집·실제 주문은 없었다.
- 두 거래일 미만·잘못된 종가의 오류 처리는 구현했지만,
  이번 실습에서 해당 오류 응답을 별도로 실행 검증하지는 않았다.