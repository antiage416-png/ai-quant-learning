# 목적:
# 일별 주가 데이터의 자료형을 지정하고,
# 종목코드의 앞자리 0과 누락된 거래량이 보존되는지 확인합니다.
#
# 흐름:
# 실습용 문자열 데이터 → DataFrame → 자료형 변환 → 검증
#
# 실행 영향:
# 인터넷 요청과 파일 저장은 없습니다.
# 아래 가격·거래량은 실제 시세가 아닌 인위적인 예시입니다.

# pandas는 표와 자료형 변환 기능을 제공합니다.
import pandas as pd


# API에서 숫자도 문자열로 받는 상황을 가정합니다.
# 두 번째 행의 거래량은 일부러 빈 문자열로 둡니다.
records = [
    {
        "stock_code": "005930",
        "market": "KRX",
        "date": "20250102",
        "open": "100",
        "high": "110",
        "low": "95",
        "close": "105",
        "volume": "1000",
    },
    {
        "stock_code": "005930",
        "market": "KRX",
        "date": "20250103",
        "open": "105",
        "high": "115",
        "low": "100",
        "close": "110",
        "volume": "",
    },
]

# 각 사전을 한 행으로 하는 표를 만듭니다.
table = pd.DataFrame(records)

# 종목코드는 계산용 숫자가 아닌 식별자입니다.
# 숫자로 바꾸지 않고 pandas의 문자열 자료형으로 지정합니다.
for column in ["stock_code", "market"]:
    table[column] = table[column].astype("string")

# YYYYMMDD 문자열을 날짜로 변환합니다.
# errors="raise"는 잘못된 날짜가 있으면 오류로 알려줍니다.
# 마지막 astype은 설계한 나노초 단위 자료형을 명시합니다.
table["date"] = pd.to_datetime(
    table["date"],
    format="%Y%m%d",
    errors="raise",
).astype("datetime64[ns]")

# 가격과 거래량에 적용할 열 목록입니다.
number_columns = ["open", "high", "low", "close", "volume"]

for column in number_columns:
    # 빈 문자열만 '값이 없음'을 뜻하는 pd.NA로 바꿉니다.
    # 0으로 채우면 실제 거래량 0과 누락을 구분할 수 없습니다.
    values = table[column].replace("", pd.NA)

    # 비어 있지 않은 값은 숫자로 변환합니다.
    # 숫자로 해석할 수 없는 문자열은 오류로 알려줍니다.
    # Int64는 정수와 누락값을 함께 표현할 수 있습니다.
    table[column] = pd.to_numeric(
        values,
        errors="raise",
    ).astype("Int64")

print("변환 결과:")
print(table.to_string(index=False))

print("\n열별 자료형:")
print(table.dtypes)

# loc[행 번호, 열 이름]으로 특정 셀의 값을 읽습니다.
# 종목코드가 원래의 6자리 문자열로 유지됐는지 검사합니다.
if table.loc[0, "stock_code"] != "005930":
    raise ValueError("종목코드의 앞자리 0이 보존되지 않았습니다.")

# isna()는 해당 값이 누락값인지 확인합니다.
if not pd.isna(table.loc[1, "volume"]):
    raise ValueError("빈 거래량이 누락값으로 유지되지 않았습니다.")

# 첫 번째 행의 정상 거래량도 그대로 유지됐는지 확인합니다.
if table.loc[0, "volume"] != 1000:
    raise ValueError("정상 거래량이 변환 중 바뀌었습니다.")

print("\n종목코드 앞자리 0 보존: 통과")
print("빈 거래량을 누락값으로 유지: 통과")
print("정상 거래량 보존: 통과")