# 목적:
# 로컬 .env 파일에서 인증 설정을 읽고 필수 값이 있는지 확인합니다.
#
# 흐름:
# .env 읽기 → 필수 값과 서버 주소 검사 → 검사 결과만 출력
#
# 실행 영향:
# 인터넷 요청과 파일 변경은 없습니다.
# 앱키·앱시크릿의 실제 값은 출력하지 않습니다.

# os: 현재 Python 프로세스의 환경변수를 읽습니다.
import os

# Path: 현재 코드 위치를 기준으로 .env 경로를 찾습니다.
from pathlib import Path

# load_dotenv: .env의 설정을 환경변수로 불러옵니다.
from dotenv import load_dotenv


# parents[2]는 이 파일에서 두 폴더 위인 학습 저장소입니다.
ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / ".env"

# 파일이 없으면 고정된 안내 문구만 출력하고 종료합니다.
# SystemExit에 문자열을 전달하면 실패 상태로 종료됩니다.
if not ENV_PATH.is_file():
    raise SystemExit("설정 검사 실패: 저장소에 .env 파일이 없습니다.")

# override=True는 같은 이름의 기존 환경변수보다 .env 값을 우선합니다.
# 변경은 실행 중인 Python 프로세스에만 적용됩니다.
load_dotenv(ENV_PATH, override=True)

# getenv()는 해당 환경변수 값을 읽습니다.
# 값이 없으면 두 번째 인수인 빈 문자열을 사용합니다.
app_key = os.getenv("KIS_APP_KEY", "").strip()
app_secret = os.getenv("KIS_APP_SECRET", "").strip()
base_url = os.getenv("KIS_BASE_URL", "").strip()

# 빈값 또는 안내용 자리표시자가 남아 있으면 준비되지 않은 상태입니다.
key_ready = bool(app_key) and app_key != "여기에_실제_APP_KEY_입력"
secret_ready = (
    bool(app_secret)
    and app_secret != "여기에_실제_APP_SECRET_입력"
)

# 실전용 키에 맞는 서버 주소가 입력됐는지 비교합니다.
url_ready = base_url == "https://openapi.koreainvestment.com:9443"

# 실제 값 대신 고정된 상태 문구만 출력합니다.
# 'A if 조건 else B'는 조건에 따라 출력할 문구를 선택합니다.
print("APP KEY:", "입력 확인" if key_ready else "미입력")
print("APP SECRET:", "입력 확인" if secret_ready else "미입력")
print("서버 주소:", "실전 주소 일치" if url_ready else "확인 필요")

# and는 세 조건이 모두 참이어야 전체가 참이 됩니다.
if not (key_ready and secret_ready and url_ready):
    raise SystemExit("설정 검사 실패: .env의 해당 항목을 확인하세요.")

print("로컬 설정 검사: 통과")
print("실제 API 인증: 아직 확인하지 않음")