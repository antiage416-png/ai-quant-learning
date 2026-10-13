# Python 3.14가 준비된 가벼운 이미지를 바탕으로 시작합니다.
FROM python:3.14-slim

# 이미지 안에서 사용할 작업 폴더를 /app으로 정합니다.
WORKDIR /app

# 프로젝트의 패키지 목록을 이미지 안의 /app으로 복사합니다.
COPY exercises/docker-day59/requirements.txt /app/requirements.txt

# 이미지 안의 Python에 목록에 적힌 패키지를 설치합니다.
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

# DB 기반 API와 DB 조회 함수를 이미지 안에 복사합니다.
COPY exercises/api-day56/main.py exercises/api-day56/price_store.py /app/exercises/api-day56/

# API가 가져와 사용하는 기존 계산 함수와 거래일 기준을 복사합니다.
COPY exercises/api-day52/main.py /app/exercises/api-day52/main.py

# API가 컨테이너 안에서 8000번 포트를 사용한다는 정보를 남깁니다.
EXPOSE 8000

# 컨테이너가 시작되면 DB 기반 API 서버를 실행합니다.
CMD ["python", "-m", "uvicorn", "main:app", "--app-dir", "/app/exercises/api-day56", "--host", "0.0.0.0", "--port", "8000"]