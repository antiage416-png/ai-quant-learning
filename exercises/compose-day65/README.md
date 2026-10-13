# 10주차 65일차 — Compose 앱·PostgreSQL 연결

실습 날짜: 2026-10-13. Compose로 API와 PostgreSQL을 실행하고 API 컨테이너의 Python에서 실제 DB 로그인과 SQL 실행을 확인했다.

## 구성

- 설정: /home/jaeho/ai-quant-learning/exercises/compose-day65/compose.yaml
- 프로젝트 quant-day65, 서비스 api와 db. 컨테이너 quant-day65-api-1·quant-day65-db-1.
- API: 기존 59일차 Dockerfile 사용, 프로젝트 루트 기준 빌드. requirements.txt에 psycopg[binary]==3.3.6 추가.
- API 포트: 127.0.0.1:8004 → 컨테이너 8000.
- 기존 SQLite: 원본 stock-day56 폴더를 /storage에 읽기 전용 bind mount. PRICE_DB_PATH=/storage/prices.db.
- PostgreSQL: postgres:17, DB quant, 사용자 quant. DB 포트 5432는 호스트에 공개하지 않았다.
- 이름 있는 볼륨: quant-day65_postgres_data → /var/lib/postgresql/data. PostgreSQL 17의 저장 경로다.
- API 접속 설정: PGHOST=db, PGPORT=5432, PGDATABASE=quant, PGUSER=quant, PGPASSWORD는 로컬 설정에서 전달.

## YAML과 저장 공간의 의미

services 아래 api와 db는 같은 단계다. api 아래 build·ports·environment·volumes는 같은 단계이며 context와 dockerfile은 build 안에 있다. 들여쓰기는 공백 두 칸 단위로 작성했다.

서비스 안의 volumes는 저장 공간 연결을 지정하고, 최상위 volumes는 이름 있는 저장 공간을 선언한다. API는 기존 폴더 bind mount, PostgreSQL은 Docker 관리 볼륨을 사용한다.

API에서 localhost는 API 자신을 가리킨다. db는 같은 Compose 네트워크의 PostgreSQL 서비스 이름이다.

## 로컬 설정

.env에 무작위 POSTGRES_PASSWORD를 생성해 저장했다. 실제 비밀번호는 문서·대화에 출력하지 않았다. 파일 권한은 600으로 지정했고 Git 제외를 확인했다. compose.yaml은 이 값을 참조한다.

.env와 DB 볼륨은 GitHub에 올라가지 않는다. 다른 환경에서는 별도 로컬 설정이 필요하다. 기존 볼륨의 계정 비밀번호는 .env를 바꾸는 것만으로 변경되지 않으므로 파일을 임의로 재생성하지 않는다.

## 실행·검사 방법

아래는 Ubuntu 터미널용이다. 호스트 가상환경 활성화는 Docker 명령에 필수가 아니다. --env-file은 로컬 설정, -f는 Compose 파일을 지정한다. config --quiet는 값 출력 없이 구조를 검사한다. 비밀번호가 노출될 수 있으므로 일반 config 출력 전체를 공유하지 않는다.

```bash
# 설정값을 출력하지 않고 구성을 검사합니다.
docker compose --env-file /home/jaeho/ai-quant-learning/exercises/compose-day65/.env -f /home/jaeho/ai-quant-learning/exercises/compose-day65/compose.yaml config --quiet

# 필요한 이미지를 다운로드·빌드하고 서비스와 저장 공간을 준비합니다.
docker compose --env-file /home/jaeho/ai-quant-learning/exercises/compose-day65/.env -f /home/jaeho/ai-quant-learning/exercises/compose-day65/compose.yaml up -d --build

# 종료된 서비스를 포함해 상태를 조회합니다.
docker compose --env-file /home/jaeho/ai-quant-learning/exercises/compose-day65/.env -f /home/jaeho/ai-quant-learning/exercises/compose-day65/compose.yaml ps -a

# PostgreSQL 서버의 접속 준비 상태를 확인합니다. 인증 성공 검사와는 다릅니다.
docker compose --env-file /home/jaeho/ai-quant-learning/exercises/compose-day65/.env -f /home/jaeho/ai-quant-learning/exercises/compose-day65/compose.yaml exec db pg_isready -U quant -d quant
```

up -d는 백그라운드 실행이며 --build는 빌드를 수행한다. 패키지 추가 후 up -d --build --no-deps api로 DB를 유지하면서 API만 재빌드·교체했다. 현재는 자동 준비 상태 대기 설정이 없으므로 접속 검사 전에 DB 준비를 확인한다.

```bash
# API 컨테이너에서 환경변수로 DB에 접속하고 읽기 전용 SQL을 실행합니다.
docker compose --env-file /home/jaeho/ai-quant-learning/exercises/compose-day65/.env -f /home/jaeho/ai-quant-learning/exercises/compose-day65/compose.yaml exec -T api python - <<'PY'
# PG 접속 환경변수를 자동으로 읽습니다. 비밀번호는 출력하지 않습니다.
import psycopg
with psycopg.connect(connect_timeout=5) as connection:
    with connection.cursor() as cursor:
        cursor.execute('SELECT current_database(), current_user, 1')
        database, user, result = cursor.fetchone()
print('접속한 DB:', database)
print('접속 사용자:', user)
print('SQL 확인값:', result)
PY
```

-T는 파이프 입력을 위해 가상 터미널 할당을 끈다. connect_timeout은 연결 대기를 5초로 제한한다. 결과는 DB quant·사용자 quant·확인값 1이었다. API 컨테이너에서 네트워크 접속·인증·SQL 실행까지 통과했다.

## 실제 범위와 다음 단계

- config 검사, 두 서비스 Up, pg_isready accepting connections, API 컨테이너의 실제 SQL 응답을 사용자 화면으로 확인했다.
- 기존 가격 조회 코드는 여전히 SQLite를 사용한다. 이번 검사로 가격 조회 API가 PostgreSQL로 전환됐다고 판단하지 않는다.
- 64일차 schema.sql은 PostgreSQL에서 아직 실행하지 않았고 가격 자료도 이관하지 않았다.
- 사용자에게 db는 서비스 이름이고 localhost는 API 컨테이너 자신이라는 점을 설명했다.
- 마무리 시 두 서비스를 stop으로 중지했고 모두 종료 코드 0을 확인했다. 컨테이너·볼륨·원본 SQLite·.env를 보관했다.
- 다음 66일차: 작은 샘플부터 SQLite 데이터를 옮겨 행 수와 값을 대조한다.

```bash
# 보관 중인 두 서비스를 다시 시작합니다. DB 준비 확인은 별도입니다.
docker compose --env-file /home/jaeho/ai-quant-learning/exercises/compose-day65/.env -f /home/jaeho/ai-quant-learning/exercises/compose-day65/compose.yaml start

# 실습 종료 시 두 서비스를 중지하고 데이터 볼륨은 보관합니다.
docker compose --env-file /home/jaeho/ai-quant-learning/exercises/compose-day65/.env -f /home/jaeho/ai-quant-learning/exercises/compose-day65/compose.yaml stop
```

참고: https://docs.docker.com/compose/ · https://hub.docker.com/_/postgres · https://www.psycopg.org/psycopg3/docs/basic/install.html
