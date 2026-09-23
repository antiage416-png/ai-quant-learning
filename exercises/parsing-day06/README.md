# HTML에서 링크를 추출해 CSV로 저장하기

## 실습 흐름
저장된 HTML → BeautifulSoup으로 제목·링크 추출 → pandas DataFrame → CSV 저장

## 실행 환경과 준비 사항
- Ubuntu WSL 터미널
- 학습 저장소의 Python 가상환경 `.venv`
- 가상환경에 beautifulsoup4와 pandas 설치
- 입력 파일: `exercises/http-day05/example.html`

## 실행 방법
아래 명령은 VS Code의 Ubuntu 터미널에서 실행한다.

```bash
# 학습 저장소로 이동합니다.
cd ~/ai-quant-learning

# 현재 터미널에서 프로젝트 가상환경을 활성화합니다.
source .venv/bin/activate

# 로컬 HTML을 분석하고 CSV를 저장합니다.
# 인터넷에 접속하지 않으며 기존 links.csv는 덮어씁니다.
python exercises/parsing-day06/parse_example.py
```

## 확인한 결과
- 페이지 제목: Example Domain
- 링크 개수: 1
- 링크 글자: Learn more
- 링크 주소: https://iana.org/domains/example
- CSV 위치: `exercises/parsing-day06/links.csv`
- CSV를 다시 읽은 결과: 1행 × 2열
- 새 터미널에서 가상환경을 활성화한 뒤 같은 결과 재현 완료

## 겪은 오류와 해결 방법
### 제목만 출력됨
- 원인: 작성한 코드에 링크 추출 부분이 없었다.
- 해결: 링크 추출 코드를 추가하고 저장한 뒤 다시 실행했다.

### Windows 파일 경로 입력 후 command not found
- 원인: Windows 파일 탐색기용 경로를 Ubuntu 터미널에 입력했다.
- 해결: Windows 파일 탐색기의 주소창에 경로를 입력했다.

## 출력 형식에서 배운 점
- 터미널에서는 DataFrame이 열 간격을 맞춘 텍스트로 출력된다.
- CSV를 표를 지원하는 프로그램으로 열면 셀 단위로 확인할 수 있다.
- CSV에는 데이터가 저장되며 색상이나 테두리 같은 서식은 저장되지 않는다.