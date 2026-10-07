# 목적: 거래일 한 행이 누락됐을 때 조회를 중단하는지 확인합니다.
# 입력 → 처리 → 결과: 원본 읽기 → 임시 사본에서 한 행 제외 → 오류 검사.
# 원본 CSV는 수정하지 않으며 인터넷 요청도 없습니다.

import sys
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

# 52일차 가격 조회 코드를 가져옵니다.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-day52"))
import main as price_api

# 원본을 읽되 종목코드의 앞자리 0을 유지합니다.
source_path = price_api.DATA_DIR / "005930_2025_clean.csv"
original = pd.read_csv(source_path, dtype=str, keep_default_na=False)

# 원본에서 제외할 거래일이 정확히 한 행인지 확인합니다.
target_date = "2025-01-03"
assert original["date"].eq(target_date).sum() == 1

# 해당 거래일을 제외한 별도 표를 만듭니다.
incomplete = original.loc[original["date"] != target_date].copy()
assert len(incomplete) == len(original) - 1

with TemporaryDirectory() as temporary:
    temporary_dir = Path(temporary)

    # 누락 자료는 임시 폴더에만 저장합니다.
    incomplete.to_csv(
        temporary_dir / "005930_2025_clean.csv",
        index=False,
        encoding="utf-8",
    )

    # 검사 동안만 임시 자료를 조회합니다.
    with patch.object(price_api, "DATA_DIR", temporary_dir):
        try:
            price_api.get_prices(
                "005930",
                date(2025, 1, 2),
                date(2025, 1, 6),
            )
        except price_api.HTTPException as error:
            assert error.status_code == 503
            assert error.detail == (
                "요청 기간에 거래일 자료가 빠져 있습니다: 2025-01-03"
            )

            print("원본 행 수:", len(original))
            print("임시 자료 행 수:", len(incomplete))
            print("오류 코드:", error.status_code)
            print("오류 설명:", error.detail)
            print("거래일 누락 검사: 통과")
        else:
            raise AssertionError(
                "거래일 자료가 누락됐는데 오류가 발생하지 않았습니다."
            )