from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd

# 지난 실습의 HTML이 저장된 폴더를 지정합니다.
current_dir = Path(__file__).resolve().parent
html_dir = current_dir.parent / "pagination-day11"

# 각 로컬 파일과 그 내용을 가져온 주소를 연결합니다.
pages = [
    ("page1.html", "https://quotes.toscrape.com/"),
    ("page2.html", "https://quotes.toscrape.com/page/2/"),
    ("page1.html", "https://quotes.toscrape.com/"),
]

rows = []

for filename, page_url in pages:
    # 저장된 HTML을 읽습니다. 인터넷에 요청하지 않습니다.
    html = (html_dir / filename).read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    quotes = soup.select("div.quote")
    first_tag = soup.select_one("div.quote span.text")

    if first_tag is not None:
        first_quote = first_tag.get_text(strip=True)
    else:
        first_quote = ""

    # 페이지 하나의 결과를 딕셔너리 하나로 담습니다.
    rows.append({
        "page_url": page_url,
        "quote_count": len(quotes),
        "first_quote": first_quote,
    })

# 두 페이지의 결과를 하나의 DataFrame으로 합칩니다.
df = pd.DataFrame(rows)

# 긴 명언 본문은 제외하고 주소와 개수만 출력합니다.
print(df[["page_url", "quote_count"]].to_string(index=False))
print("전체 행 수:", len(df))

# page_url 값이 같은 행은 첫 번째 행만 남깁니다.
unique_df = df.drop_duplicates(subset=["page_url"], keep="first")

print("\n중복 제거 전:", len(df))
print("중복 제거 후:", len(unique_df))
print(unique_df[["page_url", "quote_count"]].to_string(index=False))

# 중복을 제거한 결과를 현재 실습 폴더에 저장합니다.
csv_path = current_dir / "pages.csv"

# 행 번호는 제외하고, 한글을 읽기 쉬운 인코딩으로 저장합니다.
# 같은 이름의 파일이 있으면 덮어씁니다.
unique_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

# 저장한 CSV를 다시 읽어 결과를 확인합니다.
saved_df = pd.read_csv(csv_path, encoding="utf-8-sig")

print("저장 위치:", csv_path)
print("저장된 행·열:", saved_df.shape)
print("중복 URL 수:", saved_df.duplicated(subset=["page_url"]).sum())