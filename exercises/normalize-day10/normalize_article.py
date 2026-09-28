from urllib.parse import urljoin
from datetime import datetime

# 연습용 기준 페이지 주소입니다. 실제로 접속하지 않습니다.
base_url = "https://example.com/news/index.html"

# HTML의 href에서 추출했다고 가정한 상대주소입니다.
href = "/article/1"

# 기준 주소와 상대주소를 조합합니다.
absolute_url = urljoin(base_url, href)

print("추출한 주소:", href)
print("완성된 주소:", absolute_url)

# 웹페이지에서 추출했다고 가정한 날짜 문자열입니다.
raw_date = "2026년 9월 23일"

# 문자열의 형식을 설명해 Python의 날짜·시간 객체로 변환합니다.
parsed_date = datetime.strptime(raw_date, "%Y년 %m월 %d일")

# 원하는 형식의 문자열로 다시 만듭니다.
normalized_date = parsed_date.strftime("%Y-%m-%d")

print("원래 날짜:", raw_date)
print("정리한 날짜:", normalized_date)

# 앞뒤 공백, 연속 공백, 줄바꿈, 탭이 섞인 제목입니다.
# \n은 줄바꿈, \t는 탭을 뜻합니다.
raw_title = "  첫 번째   연습\n기사\t입니다.  "

# 공백을 기준으로 단어들을 나눕니다.
# 인수 없는 split()은 연속 공백·줄바꿈·탭을 함께 처리합니다.
words = raw_title.split()

# 단어 사이에 공백 하나를 넣어 다시 연결합니다.
normalized_title = " ".join(words)

# repr()은 줄바꿈과 탭을 \n, \t로 보여줘 비교하기 쉽습니다.
print("원래 제목:", repr(raw_title))
print("나눈 단어:", words)
print("정리한 제목:", normalized_title)