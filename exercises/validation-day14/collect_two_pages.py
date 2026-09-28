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


# 앞선 실습에서 확인한 두 페이지 주소입니다.
page_urls = [
    "https://quotes.toscrape.com/",
    "https://quotes.toscrape.com/page/2/",
]

# 두 페이지에서 추출한 모든 명언을 모을 목록입니다.
all_records = []

for page_url in page_urls:
    # 페이지를 요청하고 실제 수집 시각을 받습니다.
    html, source_url, collected_at = fetch_html(page_url)

    # 기존 함수로 현재 페이지의 명언을 추출합니다.
    records = parse_quotes(html, source_url)

    for record in records:
        # 명언 본문의 연속 공백·줄바꿈을 정리합니다.
        record["text"] = " ".join(record["text"].split())

        # 작성자가 있을 때만 공백을 정리합니다.
        if record["author"] is not None:
            record["author"] = " ".join(record["author"].split())

        # 이 페이지의 응답을 받은 시각을 기록합니다.
        record["collected_at"] = collected_at

    # 현재 페이지의 명언들을 전체 목록에 하나씩 추가합니다.
    all_records.extend(records)

    print("수집 페이지:", source_url)
    print("추출한 명언:", len(records))

print("합친 명언 수:", len(all_records))

# 명언 하나를 한 행으로 만들어 표로 정리합니다.
df = pd.DataFrame(all_records)

# 본문과 작성자가 모두 같은 명언은 첫 번째 행만 남깁니다.
unique_df = df.drop_duplicates(
    subset=["text", "author"],
    keep="first",
)

print("중복 제거 전:", len(df))
print("중복 제거 후:", len(unique_df))

# 14일차 폴더에 최종 CSV를 저장합니다.
# 같은 이름의 파일이 있으면 덮어씁니다.
csv_path = Path(__file__).resolve().parent / "quotes_two_pages.csv"
unique_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

# 저장한 파일을 다시 읽어 검증합니다.
saved_df = pd.read_csv(csv_path, encoding="utf-8-sig")

print("저장 위치:", csv_path)
print("저장된 행·열:", saved_df.shape)
print("원문 페이지 수:", saved_df["source_url"].nunique())
print(
    "중복 명언 수:",
    saved_df.duplicated(subset=["text", "author"]).sum(),
)

# 필요한 항목의 빈값 개수를 확인합니다.
required = ["text", "author", "source_url", "collected_at"]
print("필수 항목 누락:")
print(saved_df[required].isna().sum().to_string())

print("발표 시각 누락:", saved_df["published_at"].isna().sum())