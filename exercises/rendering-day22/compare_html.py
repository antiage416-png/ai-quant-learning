from urllib.request import urlopen
from bs4 import BeautifulSoup

pages = [
    ("기본 페이지", "https://quotes.toscrape.com/"),
    ("JavaScript 페이지", "https://quotes.toscrape.com/js/"),
]

for name, url in pages:
    # 서버가 보내는 HTML을 받습니다.
    with urlopen(url, timeout=20) as response:
        encoding = response.headers.get_content_charset() or "utf-8"
        html = response.read().decode(encoding)

    # JavaScript 실행 없이 HTML만 분석합니다.
    soup = BeautifulSoup(html, "html.parser")
    quotes = soup.select("div.quote")

    print(f"{name}: div.quote {len(quotes)}개")