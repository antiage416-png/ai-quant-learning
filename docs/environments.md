# 두 컴퓨터 실습 환경

최종 갱신: 2026-09-18, 한국 시간. PC 1의 Ubuntu·WSL 실행은 사용자 화면으로 확인했고, PC 2는 이전 작업 기록을 기준으로 한다.

| 항목 | PC 1 | PC 2 |
|---|---|---|
| CPU | Intel i7-11700, 논리 프로세서 16개 | Intel i5-7300HQ, 논리 프로세서 4개 |
| RAM | 16GB | 8GB |
| GPU | Intel UHD Graphics 750 | NVIDIA GTX 1050, VRAM 2GB |
| OS | Windows 10 Home 22H2 | Windows 10 Pro 22H2, 빌드 19045 |
| 디스크 | 재확인 필요 | 물리 디스크: SSD 약 120GB, HDD 약 1TB |
| C 여유 공간 | Ubuntu 설치 전 147.3GB | 정리 완료 후 15.22GB |
| D 여유 공간 | 235.3GB (설치 전 조회) | 이전 작업 전 약 875GB; 설치 이후 수치는 재확인 필요 |
| WSL | WSL 2, Ubuntu Running 확인 | 기본 버전 2, 설치된 Linux 배포판 없음 |
| Ubuntu 실행 | 26.04.1 LTS, 사용자 jaeho, 홈 /home/jaeho | 미실행·미설치 |
| Windows Anaconda | 확인 필요 | `D:\hp\DevTools\anaconda3` |

PC 2의 C가 SSD, D가 HDD라는 판단은 논리 드라이브 용량과 물리 디스크 용량을 대조한 것이다. 디스크와 파티션의 직접 매핑 명령으로 확정한 것은 아니다. 가상화 활성화와 WSL2 실제 실행 여부도 아직 검증하지 않았다.

## PC 2 Anaconda

- Anaconda Distribution 2025.12-2, Python 3.13.9, conda 25.11.1.
- 기존 391개 Python 패키지 버전을 새 설치와 비교해 모두 일치함을 확인했다.
- 추가 패키지: LightGBM 4.6.0, XGBoost 3.2.0.
- Python 실행 파일: `D:\hp\DevTools\anaconda3\python.exe`.
- Jupyter 커널: **Python (Anaconda D)** (`anaconda-d`).
- Anaconda/Jupyter/Spyder 시작 메뉴 바로가기와 사용자 PATH의 Anaconda 항목을 D로 연결했다.
- C의 이전 Anaconda 설치와 임시 보관 폴더는 삭제했고, conda 환경 목록과 Windows 제거 등록은 D 설치를 가리킨다.
- 독립 설치된 Python 3.11·3.13은 변경하지 않았다. 따라서 일반 터미널의 `python`이 반드시 Anaconda를 의미하지 않는다. Anaconda Prompt에서 활성화하거나 위 실행 파일을 명시한다.
- 예전 `ai120` Jupyter 커널은 이전부터 존재하지 않는 환경을 가리켰다. 해당 환경을 복원한 것은 아니므로 새 D 커널을 선택한다.
- Navigator·Spyder는 import와 바로가기 경로를 검사했으며 GUI 전체 조작은 미검증이다.

Windows Anaconda 이전은 WSL Ubuntu 설치와 별개다. Windows 환경을 그대로 Linux 환경으로 복사하지 않는다.

## 자원 사용 방향

PC 1은 주 개발·상대적으로 큰 백테스트·여러 컨테이너 실습, PC 2는 Python·수집·작은 백테스트·복습 중심으로 활용한다. 이는 현재 사양에 따른 계획이며 PC 1 설치 상태 확인 후 조정한다. Docker는 9주차, AWS는 17주차, Kubernetes는 21주차에 준비한다. AWS 예산과 계정 설정은 아직 정하지 않았다.

## PC 1 — 51일차 API 실습 환경 확인, 2026-10-06

- 기존 Ubuntu 가상환경: /home/jaeho/ai-quant-learning/.venv
- Python 경로: /home/jaeho/ai-quant-learning/.venv/bin/python
- 이번 실습에서 FastAPI 0.142.2와 Uvicorn 0.54.0을 설치했다.
- 두 패키지 import와 버전 출력을 확인했다.
- python -m pip check 결과: No broken requirements found.
- 로컬 주소 127.0.0.1, 포트 8000에서 상태 확인 API 응답을 확인했다.
- 브라우저와 자동 문서 호출을 확인한 뒤 Ctrl+C로 서버를 정상 종료했다.
- PC 2의 설치 상태를 확인하거나 변경한 것은 아니다.