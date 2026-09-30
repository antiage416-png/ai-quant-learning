# 목적:
# 명언 CSV와 게시글 CSV를 같은 열 구조로 정리합니다.
#
# 데이터 흐름:
# 기존 CSV 읽기 → 공통 열로 변환 → 새 CSV 저장 → 다시 읽어 검증
#
# 실행 영향:
# - 인터넷 요청은 하지 않습니다.
# - 원본 CSV와 DB는 변경하지 않습니다.
# - 이 파일과 같은 폴더에 결과 CSV 두 개를 저장합니다.
# - 같은 이름의 결과 CSV가 있으면 덮어씁니다.


# json: 원래 행을 JSON 문자열로 보관하고 다시 복원할 때 사용합니다.
import json

# Path: 파일과 폴더 경로를 다룰 때 사용합니다.
from pathlib import Path

# pandas: CSV를 표로 읽고, 변환한 표를 CSV로 저장합니다.
import pandas as pd


# __file__은 현재 Python 파일의 경로입니다.
# resolve()는 절대경로로 정리합니다.
# parents[0]: output-day28, parents[1]: exercises,
# parents[2]: ai-quant-learning 폴더입니다.
ROOT = Path(__file__).resolve().parents[2]

# parent는 현재 파일이 들어 있는 폴더입니다.
# 변환 결과를 28일차 실습 폴더에 모읍니다.
OUTPUT_DIR = Path(__file__).resolve().parent

# 두 결과 파일이 공통으로 사용할 열 이름과 순서입니다.
COMMON_COLUMNS = [
    "record_type",    # 자료 종류: quote 또는 post
    "text",           # 명언 본문 또는 게시글 제목
    "source_url",     # 자료의 출처 주소
    "collected_at",   # 원본에 기록된 수집 시각
    "original_data",  # 원래 행의 모든 필드를 담은 JSON 문자열
]


def normalize_file(name, input_path, required_columns):
    """
    CSV 하나를 읽어 공통 형식으로 변환하고 저장·검증합니다.

    입력:
    - name: 자료 종류. 이 실습에서는 quote 또는 post를 사용합니다.
    - input_path: 읽을 원본 CSV 경로입니다.
    - required_columns: 원본에 반드시 있어야 하는 열 목록입니다.

    결과:
    - 변환한 CSV를 OUTPUT_DIR에 저장합니다.
    - 검증 결과를 터미널에 출력합니다.
    - return이 없으므로 호출한 곳에 돌려주는 값은 None입니다.
    """

    # dtype=str:
    # 모든 값을 문자열로 읽어 식별자의 앞자리 0 등을 유지합니다.
    #
    # keep_default_na=False:
    # 빈칸을 pandas의 결측값 NaN으로 바꾸지 않고 빈 문자열로 읽습니다.
    original = pd.read_csv(
        input_path,
        dtype=str,
        keep_default_na=False,
    )

    # set은 값의 집합입니다.
    # 필요한 열 집합에서 실제 열 집합을 빼면 없는 열만 남습니다.
    missing = set(required_columns) - set(original.columns)

    # missing이 비어 있지 않으면 변환을 진행할 수 없습니다.
    # raise는 오류를 발생시켜 실행을 중단합니다.
    # sorted()는 없는 열 이름을 정렬해 읽기 쉽게 보여줍니다.
    if missing:
        raise ValueError(
            f"{name}: 필요한 열이 없습니다: {sorted(missing)}"
        )

    # 변환한 행을 하나씩 담을 빈 리스트입니다.
    rows = []

    # 표를 '행마다 하나의 사전'인 리스트로 바꿉니다.
    # 예: [{"post_id": "1", "title": "제목"}, ...]
    # 반복할 때마다 record에는 원본의 한 행이 들어갑니다.
    for record in original.to_dict(orient="records"):

        # 명언 CSV에는 본문·출처·수집 시각이 이미 있습니다.
        if name == "quote":
            text = record["text"]
            source_url = record["source_url"]
            collected_at = record["collected_at"]

        # 이 함수는 아래에서 quote와 post 두 종류로만 호출합니다.
        # post인 경우 게시글 CSV의 필드를 공통 열에 대응시킵니다.
        else:
            # 원본 CSV에 게시글 본문은 없으므로 제목을 사용합니다.
            # 따라서 이 text는 명언의 본문과 의미가 완전히 같지는 않습니다.
            text = record["title"]

            # 게시글 번호를 이용해 개별 게시글 주소를 구성합니다.
            # 주소 문자열만 만들며, 해당 주소로 요청하지는 않습니다.
            source_url = (
                "https://jsonplaceholder.typicode.com/posts/"
                + record["post_id"]
            )

            # 원본에 수집 시각이 없으므로 빈값으로 유지합니다.
            # 지금 시각을 넣으면 실제 수집 시각으로 오해할 수 있습니다.
            collected_at = ""

        # 공통 형식의 행 하나를 만들어 리스트에 추가합니다.
        # record_type으로 명언과 게시글을 구분할 수 있습니다.
        #
        # json.dumps()는 원래 행의 사전을 JSON 문자열로 바꿉니다.
        # 작성자·게시글 번호 등 공통 열에 없는 정보도 여기 보관합니다.
        # ensure_ascii=False는 한글 등을 읽을 수 있는 문자로 유지합니다.
        rows.append(
            {
                "record_type": name,
                "text": text,
                "source_url": source_url,
                "collected_at": collected_at,
                "original_data": json.dumps(
                    record,
                    ensure_ascii=False,
                ),
            }
        )

    # 변환한 행 리스트를 표로 만듭니다.
    # columns를 지정해 두 결과의 열 이름과 순서를 통일합니다.
    result = pd.DataFrame(rows, columns=COMMON_COLUMNS)

    # Path의 / 연산자는 폴더와 파일명을 연결합니다.
    # f 문자열은 name 값을 파일명에 넣습니다.
    # 예: quote_normalized.csv
    output_path = OUTPUT_DIR / f"{name}_normalized.csv"

    # index=False: pandas의 행 번호를 별도 열로 저장하지 않습니다.
    # utf-8-sig: Excel에서도 UTF-8 문자를 인식하기 쉽도록 저장합니다.
    result.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    # 메모리의 표뿐 아니라 실제 저장된 파일도 확인하기 위해 다시 읽습니다.
    saved = pd.read_csv(
        output_path,
        dtype=str,
        keep_default_na=False,
    )

    # JSON 문자열을 원래 형태인 사전으로 복원합니다.
    # [처리식 for 값 in 목록]은 리스트 컴프리헨션입니다.
    # original_data의 각 값을 복원해 새 리스트로 모읍니다.
    restored = [
        json.loads(value)
        for value in saved["original_data"]
    ]

    # 검증 1: 공통 열 이름과 순서가 유지됐는지 확인합니다.
    # tolist()는 pandas의 열 이름 목록을 일반 Python 리스트로 바꿉니다.
    if saved.columns.tolist() != COMMON_COLUMNS:
        raise ValueError(f"{name}: 저장된 열 구조가 다릅니다.")

    # 검증 2: 저장 전후의 행 수가 같은지 확인합니다.
    if len(saved) != len(original):
        raise ValueError(f"{name}: 저장 전후 행 수가 다릅니다.")

    # 검증 3: 복원한 원본 필드가 처음 읽은 값과 같은지 확인합니다.
    # 이것은 CSV 파일의 바이트가 아닌, 읽어 들인 행·필드 값의 비교입니다.
    if restored != original.to_dict(orient="records"):
        raise ValueError(f"{name}: 원본 필드가 보존되지 않았습니다.")

    # 위 검증을 모두 통과하면 실행 결과를 출력합니다.
    # shape는 (행 수, 열 수)입니다.
    print(f"[{name}]")
    print("원본 행·열:", original.shape)
    print("변환 행·열:", saved.shape)

    # eq("")는 빈 문자열인 행을 True로 표시합니다.
    # sum()은 True의 개수를 합산해 수집 시각이 없는 행 수를 셉니다.
    print("수집 시각 빈값:", saved["collected_at"].eq("").sum())
    print("원본 필드 보존: 통과")
    print("저장 위치:", output_path)
    print()


# 첫 번째 실행: 명언 CSV를 변환합니다.
# 아래 열들이 원본에 모두 있어야 변환을 진행합니다.
normalize_file(
    "quote",
    ROOT / "exercises/validation-day14/quotes_two_pages.csv",
    ["text", "author", "source_url", "published_at", "collected_at"],
)

# 두 번째 실행: 게시글 CSV를 같은 공통 형식으로 변환합니다.
normalize_file(
    "post",
    ROOT / "exercises/api-day26/posts.csv",
    ["post_id", "user_id", "title"],
)