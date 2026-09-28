from pathlib import Path
import pandas as pd

# 13일차에 저장한 CSV 경로를 지정합니다.
current_dir = Path(__file__).resolve().parent
csv_path = current_dir.parent / "functions-day13" / "quotes.csv"

# 기존 결과만 읽습니다.
df = pd.read_csv(csv_path, encoding="utf-8-sig")

print("검사할 명언 수:", len(df))
print("명언 본문 누락:", df["text"].isna().sum())
print("작성자 누락:", df["author"].isna().sum())

# 페이지 URL은 여러 명언이 공유하므로 중복 기준으로 단독 사용하지 않습니다.
# 같은 본문과 작성자 조합이 반복되는지 확인합니다.
duplicate_count = df.duplicated(subset=["text", "author"]).sum()
print("동일 본문·작성자 중복:", duplicate_count)

# 원문과 대조할 수 있도록 저장된 10건을 번호와 함께 출력합니다.
for number, (_, row) in enumerate(df.iterrows(), start=1):
    print(f"\n[{number}] {row['author']}")
    print(row["text"])
    print("원문:", row["source_url"])