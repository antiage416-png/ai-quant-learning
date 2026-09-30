# 목적:
# 한국투자증권 접근토큰을 발급받고 로컬에 저장해 재사용합니다.
#
# 흐름:
# 설정 읽기 → 저장된 토큰 확인 → 필요하면 발급 → 로컬 저장
#
# 실행 영향:
# 유효한 저장 토큰이 없으면 공식 인증 서버에 요청 1회를 보냅니다.
# data/private/kis_token.json을 생성하거나 갱신합니다.
# 키·토큰 값은 출력하지 않으며 시세 조회나 주문은 하지 않습니다.

import hashlib  # 어떤 앱키로 받은 토큰인지 비교할 식별값을 만듭니다.
import json     # 요청·응답과 토큰 저장 파일을 다룹니다.
import os       # 환경변수와 파일 권한을 다룹니다.
import time     # 현재 시각을 숫자로 비교합니다.

from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
TOKEN_PATH = ROOT / "data/private/kis_token.json"
REAL_URL = "https://openapi.koreainvestment.com:9443"


def get_access_token():
    """유효한 저장 토큰을 반환하거나 새로 발급·저장한 뒤 반환합니다."""

    env_path = ROOT / ".env"
    if not env_path.is_file():
        raise ValueError(".env 파일이 없습니다.")

    # 이번 Python 실행에서는 .env의 설정을 우선합니다.
    load_dotenv(env_path, override=True)
    app_key = os.getenv("KIS_APP_KEY", "").strip()
    app_secret = os.getenv("KIS_APP_SECRET", "").strip()
    base_url = os.getenv("KIS_BASE_URL", "").strip()

    if not app_key or not app_secret:
        raise ValueError("앱키 또는 앱시크릿이 비어 있습니다.")

    # 인증정보를 보낼 주소를 공식 실전 서버로 제한합니다.
    if base_url != REAL_URL:
        raise ValueError("실전 서버 주소 설정을 확인하세요.")

    # 앱키가 바뀌었을 때 예전 토큰을 재사용하지 않도록 비교합니다.
    # 해시는 비교용이며, 토큰 파일을 암호화하는 기능은 아닙니다.
    key_id = hashlib.sha256(app_key.encode("utf-8")).hexdigest()

    if TOKEN_PATH.is_file():
        # 파일이 손상됐으면 조용히 재발급하지 않고 오류로 알립니다.
        cached = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))

        same_key = cached.get("key_id") == key_id
        same_server = cached.get("base_url") == base_url

        # 만료 직전 사용을 피하도록 60초 여유를 둡니다.
        enough_time = cached.get("expires_at", 0) > time.time() + 60

        if same_key and same_server and enough_time:
            token = cached.get("access_token")
            if isinstance(token, str) and token:
                print("인증 준비: 저장된 토큰 재사용")
                return token

    # 인증에 필요한 값은 URL이 아닌 HTTPS 요청 본문에 넣습니다.
    payload = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret,
    }

    # dumps는 사전을 JSON 문자열로, encode는 전송할 바이트로 바꿉니다.
    request = Request(
        url=base_url + "/oauth2/tokenP",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    # 자동 재시도는 하지 않습니다.
    # 실패하면 원인을 확인한 뒤 다음 행동을 결정합니다.
    with urlopen(request, timeout=20) as response:
        result = json.loads(response.read().decode("utf-8"))

    token = result.get("access_token")
    expiry_text = result.get("access_token_token_expired")

    if not isinstance(token, str) or not token:
        raise ValueError("응답에서 접근토큰을 확인하지 못했습니다.")
    if not isinstance(expiry_text, str):
        raise ValueError("응답에서 만료 시각을 확인하지 못했습니다.")

    # 서버의 한국시간 만료 문자열을 시간대가 있는 날짜로 해석합니다.
    # timestamp()로 바꾸면 현재 시각과 숫자로 비교할 수 있습니다.
    expires_at = datetime.strptime(
        expiry_text, "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=ZoneInfo("Asia/Seoul")).timestamp()

    if expires_at <= time.time() + 60:
        raise ValueError("충분한 유효기간이 남은 토큰이 아닙니다.")

    cache = {
        "key_id": key_id,
        "base_url": base_url,
        "access_token": token,
        "expires_at": expires_at,
    }

    # 임시 파일에 먼저 저장한 뒤 최종 파일로 교체합니다.
    # 0o600은 소유자만 읽고 쓸 수 있는 권한입니다.
    temp_path = TOKEN_PATH.with_suffix(".tmp")
    fd = os.open(
        temp_path,
        os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
        0o600,
    )
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        json.dump(cache, file, ensure_ascii=False, indent=2)

    temp_path.replace(TOKEN_PATH)
    print("인증 성공: 토큰 발급 및 로컬 저장")
    return token


# 직접 실행할 때만 검사합니다.
# 나중에 다른 코드에서 import하면 여기서는 요청하지 않습니다.
if __name__ == "__main__":
    try:
        get_access_token()
        print("키·토큰 값: 출력하지 않음")
    except HTTPError as error:
        # 응답 본문을 그대로 출력하지 않고 상태 코드만 보여줍니다.
        status = error.code
        error.close()
        raise SystemExit(f"인증 실패: HTTP {status}") from None
    except (URLError, TimeoutError):
        raise SystemExit("인증 실패: 연결 또는 응답 시간 초과") from None
    except (ValueError, TypeError, AttributeError, OSError):
        # 예외 원문에 민감한 값이 포함될 가능성을 피합니다.
        raise SystemExit(
            "인증 준비 실패: 설정·응답 형식·로컬 파일을 확인해야 합니다."
        ) from None