# 9주차 59일차 — 분석 앱 이미지 준비

2026-10-12에 시작해 2026-10-13에 파일 작성을 마쳤다. 실제 이미지 빌드와 실행 검증은 60일차에 진행한다.

## 준비한 파일

| 파일 | 역할 |
| --- | --- |
| requirements.txt | 기존 가상환경에서 확인한 fastapi 0.142.2, uvicorn 0.54.0, pandas 3.0.6 목록 |
| Dockerfile | Python 기반 이미지 지정, 패키지 설치, 코드 복사, API 실행 지시 |
| 프로젝트 최상위 .dockerignore | .git·.venv·Python 캐시·data·환경 변수 파일을 빌드 입력에서 제외 |

Dockerfile과 requirements.txt는 /home/jaeho/ai-quant-learning/exercises/docker-day59/에 있다.
.dockerignore는 /home/jaeho/ai-quant-learning/.dockerignore에 있다.

## Dockerfile의 순서

1. FROM python:3.14-slim: Python 3.14 이미지를 기반으로 시작한다.
2. WORKDIR /app: 이미지 내부 작업 폴더를 정한다.
3. COPY와 RUN: 패키지 목록을 복사하고 이미지 제작 시 설치한다.
4. COPY: 56일차 main.py·price_store.py와 참조하는 52일차 main.py를 기존 폴더 관계대로 넣는다.
5. EXPOSE 8000: 사용하는 포트 정보를 남긴다. 실제 호스트 포트 연결은 실행 시 별도 설정한다.
6. CMD: 컨테이너 시작 시 Uvicorn으로 56일차 main:app을 실행한다.

COPY의 원본 경로는 프로젝트 최상위 폴더를 빌드 입력의 기준으로 삼는다. Dockerfile 폴더를 기준으로 빌드하지 않는다. 호스트의 .venv를 복사하지 않고 이미지 내부에 패키지를 설치한다.

## DB 연결 계획

DB는 이미지에 포함하지 않는다. .dockerignore의 data/는 호스트 원본을 삭제하지 않는다. 실행할 때 /home/jaeho/ai-quant-learning/data/stock-day56/을 컨테이너의 /app/data/stock-day56/에 읽기 전용으로 연결할 예정이다. 아직 연결 명령을 실행하지 않았다.

## 실제 확인과 한계

- 세 파일의 저장 내용, COPY 원본 파일 존재, CMD의 JSON 배열 형식을 확인했다.
- 사용자는 Dockerfile이 실행 환경·방법을 적는 파일이며, data/ 제외는 원본 삭제가 아니라는 점을 설명했다.
- EXPOSE·CMD를 터미널에 입력해 command not found가 발생했으나 Dockerfile 편집기에 추가하도록 수정했다.
- code 명령의 통신 소켓 오류로 탐색기에서 파일을 작성했다. 소켓 오류 복구는 확인하지 않았다.
- 오늘 시작 시 Docker 명령에 WSL 통합 안내가 표시됐다. 다음 실행 전에 Desktop·Ubuntu 연결을 확인한다.
- 이미지 다운로드·패키지 설치·빌드·API 실행 성공은 아직 검증하지 않았다. 의존 패키지 전체 잠금도 하지 않았다.

## 다음 60일차

Docker 연결을 확인하고 상태 확인 API를 준비한 뒤 이미지를 빌드한다. 컨테이너 포트와 읽기 전용 DB를 연결하고 상태·분석 응답을 확인한다. 현재 56일차 앱에는 상태 확인 경로가 없으므로 먼저 작은 단계로 추가한다.
