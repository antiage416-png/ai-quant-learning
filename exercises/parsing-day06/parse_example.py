from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd

# 현재 Python 파일을 기준으로 지난 실습의 HTML 경로를 계산합니다.
current_dir = Path(__file__).resolve().parent
html_path = current_dir.parent / "http-day05" / "example.html"

# 로컬 HTML 파일을 읽고 태그 구조를 분석합니다.
html = html_path.read_text(encoding="utf-8")
soup = BeautifulSoup(html, "html.parser")

# 제목을 추출합니다.
title_tag = soup.find("title")

if title_tag is not None:
    print("페이지 제목:", title_tag.get_text(strip=True))
else:
    print("title 태그가 없습니다.")

# 주소(href)가 있는 모든 링크(a 태그)를 찾습니다.
links = soup.find_all("a", href=True)
print("링크 개수:", len(links))

# 링크마다 글자와 주소를 출력합니다.
for link in links:
    print("링크 글자:", link.get_text(strip=True))
    print("링크 주소:", link["href"])

# 링크 데이터를 담을 빈 리스트를 만듭니다.
rows = []

# 링크 하나를 딕셔너리 하나로 만들어 리스트에 추가합니다.
for link in links:
    rows.append({
        "text": link.get_text(strip=True),
        "url": link["href"],
    })

# 딕셔너리의 키는 열 이름이 되고, 각 딕셔너리는 한 행이 됩니다.
df = pd.DataFrame(rows, columns=["text", "url"])

# 행 번호를 생략하고 표를 터미널에 출력합니다.
print(df.to_string(index=False))

# Python 파일과 같은 폴더에 저장할 CSV 경로를 지정합니다.
csv_path = current_dir / "links.csv"

# DataFrame을 CSV 파일로 저장합니다.
# index=False: pandas의 행 번호를 별도 열로 저장하지 않습니다.
# encoding="utf-8-sig": Excel에서도 한글을 읽기 쉽게 저장합니다.
# 같은 이름의 파일이 있으면 덮어씁니다.
df.to_csv(csv_path, index=False, encoding="utf-8-sig")

print("CSV 저장 위치:", csv_path)

# 저장한 CSV를 다시 읽어 행과 열 개수를 확인합니다.
saved_df = pd.read_csv(csv_path, encoding="utf-8-sig")
print("저장 확인:", saved_df.shape)