# 10주차 64일차 — SQL 복습과 PostgreSQL 테이블 설계

실습 날짜: 2026-10-13. 기존 SQLite 자료를 읽기 전용으로 조회하고, PostgreSQL로 옮길 가격 테이블의 기본 설계안을 작성했다. PostgreSQL에서의 생성·이관·제약조건 동작 검증은 아직 하지 않았다.

## 작성한 파일

- /home/jaeho/ai-quant-learning/exercises/sql-day64/schema.sql: PostgreSQL prices 테이블 생성 설계안.
- /home/jaeho/ai-quant-learning/exercises/sql-day64/queries.sql: 종목·기간 조건과 날짜 정렬을 적용한 조회문.

## 테이블과 규칙

한 행은 현재 KRX 자료 범위에서 한 종목의 하루 가격 정보다.

| 항목 | 자료형과 규칙 |
| --- | --- |
| stock_code | TEXT NOT NULL, 앞자리 0 보존 |
| market | TEXT NOT NULL |
| date | DATE NOT NULL |
| open·high·low·close | BIGINT NOT NULL, 각각 0보다 커야 함 |
| volume | BIGINT NOT NULL, 0 이상 |
| 기본키 | (stock_code, date) 복합 기본키 |

종목과 날짜 각각의 중복은 가능하지만 두 값의 조합은 중복을 허용하지 않는다. 가격은 이번 자료에 대해 원 단위 정수로 설계했다. 해외주식·소수점 수정주가 등 범위를 넓힐 때는 NUMERIC 등 자료형과 키의 범위를 재검토한다.

0은 값이 있고 NULL은 값이 없다는 의미다. 일반 산술에서 NULL은 결과에 전파되고 SUM 같은 집계는 보통 NULL을 제외한다. NOT NULL과 CHECK는 각각 누락과 값의 조건을 담당한다.

현재 설계는 기본안이다. 종목코드 형식, 빈 문자열, 시장 범위, 고가·저가와 시가·종가 사이의 관계 등 모든 데이터 품질 규칙을 구현한 것은 아니다.

## 실제 자료 검사

도우미가 기존 /home/jaeho/ai-quant-learning/data/stock-day56/prices.db를 읽기 전용으로 검사했다.

- 236행의 OHLC 944개 값에 소수 부분·누락·비유한 값·0 이하 가격이 없었다.
- 전체 가격 범위는 50800~298500이었다. 따라서 현재 자료의 가격을 정수로 옮길 때 소수 부분 손실이 없다.
- 거래량 누락·음수와 종목·날짜 중복 조합은 없었다.
- 원본 DB를 변경하거나 PostgreSQL로 이관하지 않았다. 모든 열의 향후 이관 적합성까지 검증한 것은 아니다.

## SQL 조회 실행

SELECT는 표시할 열, FROM은 조회할 표, WHERE는 행 조건, BETWEEN은 양 끝을 포함한 범위, ORDER BY는 정렬을 지정한다. 날짜 범위를 지정해도 없는 날짜의 행을 자동 생성하지 않는다.

Ubuntu 터미널에서 아래 방식으로 queries.sql을 실행했다. 가상환경 Python의 절대경로를 사용하므로 별도 활성화는 필요 없다. mode=ro는 DB를 읽기 전용으로 열고 파일이 없을 때 생성하지 않는다. 인터넷 요청은 없다.

```bash
# 저장한 조회 SQL을 기존 SQLite DB에서 읽기 전용으로 실행합니다.
/home/jaeho/ai-quant-learning/.venv/bin/python - <<'PY'
# SQL 파일 읽기 → DB 조회 → 결과 출력. 파일 수정은 없습니다.
from pathlib import Path
import sqlite3

root = Path('/home/jaeho/ai-quant-learning')
sql = (root / 'exercises/sql-day64/queries.sql').read_text(encoding='utf-8')
db_path = root / 'data/stock-day56/prices.db'

# PostgreSQL용 schema.sql은 실행하지 않습니다.
with sqlite3.connect(db_path.as_uri() + '?mode=ro', uri=True) as connection:
    rows = connection.execute(sql).fetchall()

for stock_code, day, close in rows:
    print('종목:', stock_code, '날짜:', day, '종가:', close)
print('조회 행 수:', len(rows))
PY
```

사용자 실행 결과:

| 종목 | 날짜 | 종가 |
| --- | --- | ---: |
| 000660 | 2025-01-02 | 171200.0 |
| 000660 | 2025-01-03 | 181900.0 |
| 000660 | 2025-01-06 | 199800.0 |

조회 행 수는 3이었다. 1월 4·5일은 주말로 저장된 거래 자료가 없다. .0 표시는 기존 SQLite 가격이 REAL이기 때문이다.

## 이해 확인과 다음 단계

사용자는 종목·날짜 조합으로 행을 구분할 수 있고, 날짜 조건이 없으면 해당 종목의 모든 날짜 자료를 조회한다고 답했다. 거래량 0과 누락을 구분했으며 중복 방지 기준을 고유값 설정이라고 설명해 복합 기본키 용어로 정리했다. 독립적인 설계·구현 숙련도까지 확인한 것은 아니다.

다음 65일차에는 Compose에 앱과 PostgreSQL을 정의하고 연결 상태를 확인한다. 현재 API는 SQLite를 사용하므로 PostgreSQL 컨테이너 실행만으로 앱의 DB 연결이 자동 전환되지는 않는다.

참고: https://www.postgresql.org/docs/current/ddl-constraints.html
