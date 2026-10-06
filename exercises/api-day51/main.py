# 목적: 상태 확인 API를 연결할 앱 객체를 만듭니다.
# 입력 → 처리 → 결과: 앱 제목 → FastAPI 객체 생성 → app에 저장.
# 이 코드 자체는 서버를 실행하거나 파일을 저장하지 않습니다.

# FastAPI는 요청 경로와 처리 함수를 등록할 앱을 만드는 클래스입니다.
from fastapi import FastAPI

# 만든 앱을 app이라는 변수에 저장합니다.
# title은 나중에 자동 API 문서 화면에 표시될 이름입니다.
app = FastAPI(title="주식 분석 학습 API")

# /api/health 주소로 GET 요청이 오면 아래 함수를 실행하도록 등록합니다.
@app.get("/api/health")
def health_check():
    # 상태 확인용 딕셔너리를 반환하면 FastAPI가 JSON 응답으로 전달합니다.
    return {"status": "ok"}