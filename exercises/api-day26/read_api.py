import json
from urllib.request import urlopen
import pandas as pd
from pathlib import Path

# 가상 게시글 목록을 제공하는 공개 API입니다.
url = "https://jsonplaceholder.typicode.com/posts"

with urlopen(url, timeout=20) as response:
    body = response.read().decode("utf-8")
    print("응답 상태:", response.status)

# JSON 문자열을 Python 데이터로 변환합니다.
posts = json.loads(body)

print("변환된 자료형:", type(posts).__name__)
print("게시글 수:", len(posts))

# 목록의 첫 번째 게시글을 확인합니다.
first_post = posts[0]

print("첫 게시글의 항목:", list(first_post.keys()))
print("첫 게시글 번호:", first_post["id"])
print("첫 게시글 제목:", first_post["title"])

# 게시글 딕셔너리 목록을 표로 변환합니다.
df = pd.DataFrame(posts)

# 이번에 사용할 열만 선택합니다.
table = df[["id", "userId", "title"]].copy()

# 열 이름을 의미가 드러나도록 바꿉니다.
table = table.rename(columns={
    "id": "post_id",
    "userId": "user_id",
})

# 터미널에서는 첫 5행만 텍스트로 출력합니다.
print(table.head(5).to_string(index=False))
print("전체 행·열:", table.shape)

# 현재 Python 파일과 같은 폴더에 저장합니다.
csv_path = Path(__file__).resolve().parent / "posts.csv"

# 행 번호는 제외하고 저장합니다.
# 같은 이름의 파일이 있으면 덮어씁니다.
table.to_csv(csv_path, index=False, encoding="utf-8-sig")

# 저장된 CSV를 다시 읽어 검증합니다.
saved = pd.read_csv(csv_path, encoding="utf-8-sig")

print("저장 위치:", csv_path)
print("저장된 행·열:", saved.shape)
print("게시글 번호 중복:", saved.duplicated(subset=["post_id"]).sum())
print("열별 누락:")
print(saved.isna().sum().to_string())