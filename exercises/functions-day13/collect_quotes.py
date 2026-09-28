from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import urlopen
from datetime import datetime, timezone


# HTML과 출처 주소를 받아 명언 목록을 반환하는 함수입니다.
# 주소를 받아 HTML, 최종 응답 주소, 수집 시각을 반환합니다.
def fetch_html(url):
    # 네트워크 작업의 대기 시간을 제한해 요청합니다.
    with urlopen(url, timeout=20) as response:
        body = response.read()

        # 응답 본문을 모두 받은 직후의 시각을 UTC로 기록합니다.
        collected_at = datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        )

        # 다른 주소로 이동된 경우를 반영한 최종 주소입니다.
        source_url = response.geturl()

        # 응답 헤더의 문자 인코딩을 사용하고, 없으면 UTF-8을 사용합니다.
        encoding = response.headers.get_content_charset() or "utf-8"
        html = body.decode(encoding)

    return html, source_url, collected_at

def parse_quotes(html, source_url):
    soup = BeautifulSoup(html, "html.parser")
    rows = []

    for quote in soup.select("div.quote"):
        text_tag = quote.select_one("span.text")
        author_tag = quote.select_one("small.author")

        # 명언 본문이 없는 항목은 건너뜁니다.
        if text_tag is None:
            continue

        text = text_tag.get_text(" ", strip=True)

        if author_tag is not None:
            author = author_tag.get_text(strip=True)
        else:
            author = None

        rows.append({
            "text": text,
            "author": author,
            "source_url": source_url,
            "published_at": None,
        })

    return rows


# 첫 페이지를 실제로 요청합니다.
html, source_url, collected_at = fetch_html(
    "https://quotes.toscrape.com/"
)

# 받은 HTML을 기존 추출 함수에 전달합니다.
records = parse_quotes(html, source_url)

# 같은 응답에서 추출한 모든 명언에 수집 시각을 추가합니다.
for record in records:
    record["collected_at"] = collected_at

print("추출한 명언 수:", len(records))

if records:
    print("작성자:", records[0]["author"])
    print("원문 페이지:", records[0]["source_url"])
    print("발표 시각:", records[0]["published_at"])
    print("수집 시각:", records[0]["collected_at"])

# 저장할 열과 순서를 지정합니다.
columns = [
    "text",
    "author",
    "source_url",
    "published_at",
    "collected_at",
]

df = pd.DataFrame(records, columns=columns)

# 현재 Python 파일과 같은 폴더에 저장합니다.
csv_path = Path(__file__).resolve().parent / "quotes.csv"

# None은 CSV에서 빈칸으로 저장됩니다.
# 같은 이름의 파일이 있으면 덮어씁니다.
df.to_csv(csv_path, index=False, encoding="utf-8-sig")

# 저장된 파일을 다시 읽어 확인합니다.
saved_df = pd.read_csv(csv_path, encoding="utf-8-sig")

print("저장 위치:", csv_path)
print("저장된 행·열:", saved_df.shape)
print("원문 주소 누락:", saved_df["source_url"].isna().sum())
print("수집 시각 누락:", saved_df["collected_at"].isna().sum())
print("발표 시각 누락:", saved_df["published_at"].isna().sum())