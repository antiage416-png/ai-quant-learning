import logging
from pathlib import Path

# 현재 Python 파일과 같은 폴더에 로그를 저장합니다.
log_path = Path(__file__).resolve().parent / "practice.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        # 터미널에 출력합니다.
        logging.StreamHandler(),

        # 파일에도 기록합니다.
        # mode="a"는 기존 내용 뒤에 추가한다는 뜻입니다.
        logging.FileHandler(log_path, mode="a", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)

# 실제 요청 없이 출력과 저장을 확인하는 연습 메시지입니다.
logger.info("로그 실습을 시작합니다.")
logger.warning("연습 메시지: 요청이 제한되면 기다렸다가 재시도합니다.")
logger.error("연습 메시지: 최대 시도 횟수에 도달했습니다.")
logger.info("로그 실습이 끝났습니다.")