from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen
from bs4 import BeautifulSoup

# 저장한 첫 페이지 HTML의 경로를 구합니다.
current_dir = Path(__file__).resolve().parent
html_path = current_dir / "page1.html"

# 첫 페이지를 받은 주소입니다.
page_url = "https://quotes.toscrape.com/"

# 로컬 HTML을 읽어 분석합니다.
html = html_path.read_text(encoding="utf-8")
soup = BeautifulSoup(html, "html.parser")

# 첫 페이지에서 Next 링크를 찾습니다.
next_link = soup.select_one("li.next a[href]")

if next_link is not None:
    # 링크의 상대주소를 꺼내 절대주소로 바꿉니다.
    href = next_link["href"]
    next_url = urljoin(page_url, href)

    print("링크 글자:", next_link.get_text(strip=True))
    print("HTML의 주소:", href)
    print("다음 페이지 주소:", next_url)

    # 찾은 주소로 요청하고 응답 본문을 읽습니다.
    # timeout은 네트워크 작업의 대기 시간을 제한합니다.
    with urlopen(next_url, timeout=20) as response:
        page2_bytes = response.read()
        print("두 번째 페이지 응답:", response.status)

    # 받은 HTML을 파일로 저장합니다.
    # 같은 이름의 파일이 있으면 덮어씁니다.
    page2_path = current_dir / "page2.html"
    page2_path.write_bytes(page2_bytes)

    print("저장 위치:", page2_path)
    print("저장 크기:", len(page2_bytes), "바이트")

else:
    print("다음 페이지 링크가 없습니다.")

# 저장된 두 페이지에서 명언 개수와 첫 명언을 비교합니다.
for filename in ["page1.html", "page2.html"]:
    saved_html = (current_dir / filename).read_text(encoding="utf-8")
    saved_soup = BeautifulSoup(saved_html, "html.parser")

    # quote 클래스의 div 하나가 명언 한 항목입니다.
    quotes = saved_soup.select("div.quote")

    # 첫 명언의 본문을 찾습니다.
    first_text = saved_soup.select_one("div.quote span.text")

    print(f"\n파일: {filename}")
    print("명언 개수:", len(quotes))

    if first_text is not None:
        print("첫 명언:", first_text.get_text(strip=True))
    else:
        print("명언 본문을 찾지 못했습니다.")