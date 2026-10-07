# 목적: 기존 삼성전자 백테스트를 실행·저장하고 실행 ID로 결과를 조회합니다.
# 입력 → 처리 → 결과: 실행 요청 → 계산·검사·JSON 저장 → ID와 결과 반환.
# 조회 요청은 저장된 JSON을 읽어 반환합니다.
# POST는 data/stock-day53/runs에 새 결과 파일을 만듭니다.
# 직접 실행 시에는 ID 저장 연습 코드가 실행됩니다.
# 외부 데이터 요청과 실제 주문은 없습니다.

# 파이썬 표준 라이브러리의 식별자 생성 함수를 가져옵니다.
from uuid import uuid4
# 실행 기록을 JSON 파일에 저장할 때 사용합니다.
import json

# 저장할 폴더와 파일 경로를 만들 때 사용합니다.
from pathlib import Path

# 기존 계산 코드가 있는 폴더를 파이썬의 검색 경로에 추가합니다.
import sys
# 정확한 십진수 금액을 JSON 저장용 문자열로 바꿀 때 사용합니다.
from decimal import Decimal
# 조회 API와 오류 응답을 만드는 도구입니다.
from fastapi import FastAPI, HTTPException

# 주소로 받은 실행 ID가 올바른 UUID 형식인지 검사합니다.
from uuid import UUID



COST_CODE_DIR = (
    Path(__file__).resolve().parents[2] / "exercises" / "costs-day44"
)
sys.path.insert(0, str(COST_CODE_DIR))

# 44일차 코드에서 입력 읽기·계산·검사·요약·비용 설정 함수를 가져옵니다.
from build_cost_ledgers import (
    read_input,
    simulate,
    check_ledger,
    summarize,
    load_settings,
)

# 식별자 객체를 저장·응답에 쓰기 편한 문자열로 바꿉니다.
# 호출할 때마다 새 실행 ID를 문자열로 반환합니다.
def create_run_id():
    return str(uuid4())

# 기록과 저장 폴더를 받아 JSON 파일을 만들고 파일 경로를 반환합니다.
def save_record(record, directory):
    directory.mkdir(parents=True, exist_ok=True)
    record_path = directory / f"{record['run_id']}.json"

    # 기존 파일을 덮어쓰지 않고 새 기록을 저장합니다.
    with record_path.open("x", encoding="utf-8") as file:
        json.dump(record, file, ensure_ascii=False, indent=2)

    return record_path


# 서버가 사용할 앱과 실제 백테스트 결과 폴더를 준비합니다.
app = FastAPI(title="백테스트 실행·조회 학습 API")
RUNS_DIR = Path(__file__).resolve().parents[2] / "data" / "stock-day53" / "runs"


# 주소의 실행 ID에 해당하는 저장 파일을 읽어 반환합니다.
@app.get("/api/backtests/{run_id}")
def get_backtest(run_id: UUID):
    result_path = RUNS_DIR / f"{run_id}.json"

    # 해당 ID의 결과가 없으면 조회 실패를 알립니다.
    if not result_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="해당 실행 ID의 백테스트 결과가 없습니다.",
        )

    with result_path.open("r", encoding="utf-8") as file:
        return json.load(file)

    
# 파일을 직접 실행할 때만 두 번 호출해 결과를 확인합니다.
if __name__ == "__main__":
    first_id = create_run_id()
    second_id = create_run_id()

    print("첫 번째 실행 ID:", first_id)
    print("두 번째 실행 ID:", second_id)
    print("두 ID가 다른가:", first_id != second_id)

    # 코드 파일 위치를 기준으로 학습 저장소를 찾습니다.
    root = Path(__file__).resolve().parents[2]

    # ID 저장 연습용 폴더를 만듭니다.
    practice_dir = root / "data" / "stock-day53" / "id_practice"
    practice_dir.mkdir(parents=True, exist_ok=True)

    # 첫 번째 ID와 이 기록의 용도를 저장합니다.
    record = {
        "run_id": first_id,
        "record_type": "실행 ID 저장 연습",
        "backtest_calculated": False,
    }

    # 저장 함수에 기록과 폴더를 전달하고 파일 경로를 받습니다.
    record_path = save_record(record, practice_dir)

    print("기록 저장 위치:", record_path)

        # 저장한 JSON 파일을 다시 읽어 딕셔너리로 복원합니다.
    with record_path.open("r", encoding="utf-8") as file:
        saved_record = json.load(file)

    print("다시 읽은 기록:", saved_record)
    print("저장 전후 내용이 같은가:", saved_record == record)
    print("백테스트 계산 함수 불러오기:", callable(simulate))

# 기존 조건으로 계산·검사·저장하고 결과 기록을 반환합니다.
def run_backtest():
    root = Path(__file__).resolve().parents[2]

    # 기존 삼성전자 가격 자료를 읽고 기본 형식을 검사합니다.
    prices = read_input(
        root / "data" / "stock-day33" / "clean" / "005930_2025_clean.csv",
        ["stock_code", "date", "open", "close"],
    )

    # 40일차에서 이미 다음 거래일에 배치한 주문 자료를 읽습니다.
    signals = read_input(
        root / "data" / "stock-day40" / "005930_2025_signals.csv",
        [
            "stock_code", "date", "open", "close_signal",
            "previous_signal", "previous_date", "open_order",
        ],
    )

    # 44일차의 기존 초기 자금·수수료·세금·슬리피지 설정을 읽습니다.
    settings = load_settings()

    print("가격 자료:", len(prices), "행")
    print("주문 자료:", len(signals), "행")
    print("가격 기간:", prices["date"].iloc[0], "~", prices["date"].iloc[-1])
    print("초기 자금:", settings["initial_cash"], "원")

        # 이번 실행이 기존 2025년 전체 기간인지 확인합니다.
    if (
        len(prices) != 242
        or prices["date"].iloc[0] != "2025-01-02"
        or prices["date"].iloc[-1] != "2025-12-30"
    ):
        raise ValueError("기존 실습의 가격 자료 행 수 또는 기간과 다릅니다.")

    # 가격과 주문을 같은 거래일끼리 연결할 수 있는지 확인합니다.
    if prices["date"].tolist() != signals["date"].tolist():
        raise ValueError("가격 자료와 주문 자료의 거래일이 다릅니다.")

    print("가격·주문 자료의 기간과 거래일 대조: 통과")

        # 각 거래일에 대응하는 직전 거래일의 날짜와 신호를 만듭니다.
    previous_dates = prices["date"].shift(1).fillna("")
    previous_signals = signals["close_signal"].shift(1).fillna("없음")

    # 주문 파일에 기록된 전날 날짜와 신호가 맞는지 확인합니다.
    if signals["previous_date"].fillna("").tolist() != previous_dates.tolist():
        raise ValueError("주문 자료의 전날 날짜 연결이 다릅니다.")

    if signals["previous_signal"].fillna("없음").tolist() != previous_signals.tolist():
        raise ValueError("주문 자료의 전날 신호 연결이 다릅니다.")

    # 계산에 사용할 주문을 기존 파일에서 그대로 가져옵니다.
    actions = signals["open_order"].tolist()

    # 매수·매도 주문이 각각 올바른 전날 신호에 연결됐는지 검사합니다.
    for action, signal in zip(actions, previous_signals):
        if action not in {"매수", "매도", "없음"}:
            raise ValueError("알 수 없는 주문이 있습니다.")
        if action == "매수" and signal != "골든크로스":
            raise ValueError("매수 주문과 전날 골든크로스가 연결되지 않습니다.")
        if action == "매도" and signal != "데드크로스":
            raise ValueError("매도 주문과 전날 데드크로스가 연결되지 않습니다.")

    print("전날 날짜·신호와 주문 연결 검사: 통과")

        # 주문이 있는 날에는 근거가 된 전날 날짜를 기록합니다.
    signal_dates = [
        previous_date if action != "없음" else ""
        for previous_date, action in zip(previous_dates, actions)
    ]

    # 기존 가격·주문·비용 설정으로 일별 장부를 계산합니다.
    ledger = simulate(
        prices,
        actions,
        signal_dates,
        settings,
        "교차 전략",
    )

    # 장부의 현금·수량·비용 연결을 검사합니다.
    check_ledger(ledger, settings["initial_cash"])

    # 계산한 장부에서 성과 요약을 만듭니다.
    summary = summarize(
        ledger,
        "비용 반영",
        settings["initial_cash"],
    )

    print("장부 행 수:", len(ledger))
    print("최종 자산:", summary["final_equity"], "원")
    print("기간 수익률:", summary["return_pct"], "%")
    print("장부 연결 검사: 통과")

        # Decimal 금액·비율은 정밀도를 보존하도록 문자열로 바꿉니다.
    # 정수 개수와 일반 문자열은 그대로 유지합니다.
    saved_summary = {
        key: str(value) if isinstance(value, Decimal) else value
        for key, value in summary.items()
    }

    # 계산 결과와 실행 조건을 하나의 기록으로 묶습니다.
    result = {
        "run_id": create_run_id(),
        "record_type": "백테스트 결과",
        "backtest_calculated": True,
        "stock_code": "005930",
        "start_date": prices["date"].iloc[0],
        "end_date": prices["date"].iloc[-1],
        "rows": len(ledger),
        "settings": {
            key: str(value) for key, value in settings.items()
        },
        "summary": saved_summary,
    }

    # 실제 계산 결과는 연습 기록과 구분한 폴더에 저장합니다.
    result_path = save_record(
        result,
        root / "data" / "stock-day53" / "runs",
    )

    print("백테스트 실행 ID:", result["run_id"])
    print("백테스트 결과 저장 위치:", result_path)

    # 저장한 백테스트 결과를 다시 읽습니다.
    with result_path.open("r", encoding="utf-8") as file:
        reread_result = json.load(file)

    # 실행 조건과 계산 요약을 포함한 전체 기록을 비교합니다.
    if reread_result != result:
        raise ValueError("백테스트 결과의 저장 전후 내용이 다릅니다.")

    print("백테스트 결과 저장·재읽기 비교: 통과")
    print("다시 읽은 최종 자산:", reread_result["summary"]["final_equity"], "원")
    # 계산하고 저장한 결과를 호출한 곳에 전달합니다.
    return result

# POST 요청을 받으면 새로 계산하고 실행 ID와 결과를 반환합니다.
@app.post("/api/backtests", status_code=201)
def create_backtest():
    return run_backtest()