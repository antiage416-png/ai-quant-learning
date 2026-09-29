import logging
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup

# 터미널과 파일에 같은 로그를 남깁니다.
log_path = Path(__file__).resolve().parent / "collection.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_path, mode="a", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)

# 정상 페이지와 오류 확인용 주소입니다.
urls = [
    "https://quotes.toscrape.com/",
    "https://quotes.toscrape.com/practice-missing-page-day15/",
]

success_count = 0
failure_count = 0
total_quotes = 0

logger.info("수집 시작: 대상 %d개", len(urls))

for url in urls:
    logger.info("요청 시작: %s", url)

    try:
        with urlopen(url, timeout=20) as response:
            body = response.read()
            encoding = response.headers.get_content_charset() or "utf-8"
            html = body.decode(encoding)
            status = response.status

        soup = BeautifulSoup(html, "html.parser")
        quote_count = len(soup.select("div.quote"))

        success_count += 1
        total_quotes += quote_count

        logger.info(
            "수집 성공: 상태=%d, 명언=%d개, 주소=%s",
            status,
            quote_count,
            url,
        )

    except HTTPError as error:
        failure_count += 1
        logger.error("HTTP 실패: 상태=%d, 주소=%s", error.code, url)
        error.close()

    except (URLError, TimeoutError) as error:
        failure_count += 1
        logger.error("연결 또는 대기 시간 오류: 주소=%s, 이유=%s", url, error)

logger.info(
    "수집 종료: 성공=%d, 실패=%d, 명언=%d개",
    success_count,
    failure_count,
    total_quotes,
)