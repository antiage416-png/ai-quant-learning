from pathlib import Path
from bs4 import BeautifulSoup

# 이 Python 파일과 같은 폴더의 HTML 경로를 지정합니다.
current_dir = Path(__file__).resolve().parent
html_path = current_dir / "articles.html"

# 로컬 HTML을 읽고 태그 구조를 분석합니다.
html = html_path.read_text(encoding="utf-8")
soup = BeautifulSoup(html, "html.parser")

# article 태그이면서 news-item 클래스를 가진 요소를 모두 찾습니다.
articles = soup.select("article.news-item")

print("기사 개수:", len(articles))

# 각 기사 안에서 제목을 찾아 출력합니다.
# enumerate(..., start=1)은 기사에 1부터 번호를 붙입니다.
for number, article in enumerate(articles, start=1):
    title_tag = article.select_one("h2.title")

    # 제목 태그가 없을 때도 오류 없이 처리합니다.
    if title_tag is not None:
        title = title_tag.get_text(strip=True)
    else:
        title = "제목 없음"

    print(f"{number}. {title}")

        # 현재 기사 안에서 published 클래스의 time 태그를 찾습니다.
    date_tag = article.select_one("time.published")

    if date_tag is not None:
        # datetime 속성값을 가져옵니다.
        # 속성이 없으면 대신 "날짜 없음"을 사용합니다.
        date = date_tag.get("datetime", "날짜 없음")
    else:
        # time 태그 자체가 없는 경우입니다.
        date = "날짜 없음"

    print(f"   날짜: {date}")

        # 현재 기사의 제목 안에서 href 속성이 있는 a 태그를 찾습니다.
    link_tag = article.select_one("h2.title a[href]")

    if link_tag is not None:
        # 선택할 때 href의 존재를 확인했으므로 속성값을 꺼냅니다.
        url = link_tag["href"]
    else:
        # 조건에 맞는 링크가 없으면 안내 문구를 사용합니다.
        url = "링크 없음"

    print(f"   링크: {url}")