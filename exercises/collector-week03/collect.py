import json
import time
from datetime import datetime, timezone
from urllib.request import urlopen
from bs4 import BeautifulSoup
from storage import save_quotes
import logging
from pathlib import Path
from urllib.error import HTTPError, URLError

# 실행 기록을 터미널과 collector.log에 함께 남깁니다.
log_path = Path(__file__).resolve().parent / "collector.log"

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


def fetch_html(url, max_attempts=3):
    """HTML을 요청하고, 초 단위 Retry-After가 있는 429만 재시도합니다."""
    for attempt in range(1, max_attempts + 1):
        logger.info("요청 시도 %d/%d: %s", attempt, max_attempts, url)

        try:
            with urlopen(url, timeout=20) as response:
                body = response.read()
                collected_at = datetime.now(timezone.utc).isoformat(
                    timespec="seconds"
                )
                source_url = response.geturl()
                encoding = (
                    response.headers.get_content_charset() or "utf-8"
                )

            return body.decode(encoding), source_url, collected_at

        except HTTPError as error:
            # 429 이외의 오류나 마지막 실패는 호출한 쪽에 전달합니다.
            if error.code != 429 or attempt == max_attempts:
                raise

            retry_after = error.headers.get("Retry-After")

            # 현재는 초 단위 값만 지원합니다.
            if retry_after is None:
                raise

            retry_after = retry_after.strip()

            if not retry_after.isascii() or not retry_after.isdigit():
                raise

            wait_seconds = int(retry_after)

            # 실습에서 너무 오래 기다려야 하면 재시도하지 않습니다.
            # 서버의 대기 시간을 줄여서 요청하는 것이 아니라 중단합니다.
            if wait_seconds > 60:
                logger.warning("대기 시간이 60초를 초과해 재시도를 중단합니다.")
                raise

            error.close()

            logger.warning(
                "HTTP 429: %d초 대기 후 재시도", wait_seconds
            )
            time.sleep(wait_seconds)


def parse_quotes(html, source_url, collected_at):
    """HTML에서 저장할 명언 목록과 제외 건수를 만듭니다."""
    soup = BeautifulSoup(html, "html.parser")
    records = []
    skipped_count = 0

    for quote in soup.select("div.quote"):
        text_tag = quote.select_one("span.text")
        author_tag = quote.select_one("small.author")

        # 본문이나 작성자 태그가 없으면 제외합니다.
        if text_tag is None or author_tag is None:
            skipped_count += 1
            continue

        text = " ".join(text_tag.get_text(" ", strip=True).split())
        author = " ".join(author_tag.get_text(" ", strip=True).split())

        # 태그는 있지만 글자가 비어 있는 경우도 제외합니다.
        if not text or not author:
            skipped_count += 1
            continue

        records.append({
            "text": text,
            "author": author,
            "source_url": source_url,
            "published_at": None,
            "collected_at": collected_at,
        })

    return records, skipped_count

def collect_one(url):
    """주소 하나를 수집합니다. 실패하면 실패 정보를 반환합니다."""
    logger.info("수집 시작: %s", url)

    try:
        html, source_url, collected_at = fetch_html(url)
        records, skipped_count = parse_quotes(
            html, source_url, collected_at
        )
        total = save_quotes(records)

        logger.info(
            "수집·저장 성공: 추출=%d, 제외=%d, DB전체=%d",
            len(records),
            skipped_count,
            total,
        )

        # 성공했으므로 실패 정보가 없습니다.
        return None

    except HTTPError as error:
        reason = f"HTTP {error.code}"
        logger.error("HTTP 실패: 상태=%d, 주소=%s", error.code, url)
        error.close()

        return {"url": url, "reason": reason}

    except (URLError, TimeoutError) as error:
        logger.error(
            "연결 또는 대기 시간 오류: 주소=%s, 이유=%s",
            url,
            error,
        )

        return {"url": url, "reason": str(error)}


# 이 파일을 직접 실행했을 때만 아래 작업을 수행합니다.
if __name__ == "__main__":
    # 정상 페이지 두 개와 실패 기록 확인용 주소 하나입니다.
    urls = [
        "https://quotes.toscrape.com/",
        "https://quotes.toscrape.com/page/2/",
        "https://quotes.toscrape.com/practice-missing-page-day15/",
    ]

    failures = []
    success_count = 0

    for number, url in enumerate(urls, start=1):
        # 서로 다른 페이지 요청 사이에도 기본 간격을 둡니다.
        if number > 1:
            logger.info("다음 주소 요청 전 2초 대기")
            time.sleep(2)

        failure = collect_one(url)

        if failure is None:
            success_count += 1
        else:
            failures.append(failure)

    # 이번 실행의 실패 목록으로 파일을 갱신합니다.
    failure_path = Path(__file__).resolve().parent / "failed_urls.json"
    failure_path.write_text(
        json.dumps(failures, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info(
        "전체 수집 종료: 대상=%d, 성공=%d, 실패=%d",
        len(urls),
        success_count,
        len(failures),
    )