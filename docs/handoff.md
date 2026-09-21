# 다른 컴퓨터에서 이어가기

최종 갱신: 2026-09-18. 이전 대화가 보이지 않으면 이 문서와 루트 AGENTS.md부터 읽는다.

## 프로젝트와 진행 위치

한국 주식 일봉·공시 데이터를 수집하고 백테스트, AI 분석 에이전트, 모의투자 서비스를 구현하는 24주 학습 계획이다. 실거래는 범위 밖이다. 평일 3시간·주말 4시간을 기준으로 개념 → 한 가지 실습 → 결과 확인 → 기록 순서로 진행한다.

PC 2의 환경 정리·Anaconda 이전에 이어 PC 1의 Ubuntu 설치·계정 생성·WSL 2 실행 확인을 완료했다. PC 1은 Ubuntu 26.04.1 LTS, 사용자 jaeho, 홈 /home/jaeho이다. 1주차 2일차의 설치·실행 확인까지 진행했으며 패키지 업데이트는 아직 미확인이다. PC 2에는 Ubuntu를 아직 설치하지 않았다.

## 먼저 실행할 순서

1. PC 1의 기존 `ai-quant-learning` 저장소 폴더에서 `git status`를 확인한다.
2. 변경 사항이 있으면 먼저 검토·저장한다. 깨끗한 상태에서 `git pull --ff-only`를 실행한다. 충돌은 강제 push나 reset으로 덮어쓰지 않는다.
3. [9월 18일 기록](../daily/2026-09-18.md)과 [환경표](environments.md)를 읽는다.
4. PC 1에서 VS Code의 WSL: Ubuntu 연결을 화면으로 확인했다. VS Code 터미널의 whoami 결과 jaeho, pwd 결과 /home/jaeho를 사용자 화면으로 확인했다. Windows 학습 저장소의 최근 커밋 push 여부와 Ubuntu 작업 사본 존재 여부를 확인한 뒤 작업 폴더 연결을 진행한다.
5. Ubuntu 작업 폴더 준비 후 패키지 업데이트를 진행한다. 업데이트 결과를 확인한 뒤 1주차 3일차의 파일·폴더 명령 실습으로 넘어간다. WSL 자원 설정은 아직 변경하지 않았다.

저장소가 없는 컴퓨터에서만 다음 명령으로 새 사본을 만든다. 비공개 저장소이므로 해당 GitHub 계정 인증이 필요하다.

```powershell
# 원격 저장소를 현재 폴더 아래 ai-quant-learning 폴더로 다운로드한다. 로컬 파일이 생성된다.
git clone https://github.com/antiage416-png/ai-quant-learning.git
# 내려받은 저장소 폴더로 이동한다. cd는 작업 위치를 바꾸는 명령이다.
cd ai-quant-learning
```

## PC 2에서 완료한 것

- 개인 자료 4,593개 이동·무결성 검사, 기존 경로는 정션으로 유지.
- 캐시·설치 잔여 파일 541개 정리.
- Anaconda를 D에 재설치, 391개 패키지 버전 일치, 계산·실제 Jupyter 실행 검사 통과.
- 기존 C 설치 경로 없이 재검증 후 C 설치 삭제. 최종 C 여유 공간 15.22GB.
- 새 Anaconda 위치: `D:\hp\DevTools\anaconda3`, 커널: **Python (Anaconda D)**.

이 경로와 폴더 정리 스크립트는 PC 2 전용이다. PC 1에 그대로 적용하지 않는다. 독립 Python 설치는 보존했으며 일반 `python` 명령이 Anaconda와 다를 수 있다.

## 남은 확인

- PC 1: Ubuntu 패키지 업데이트 미확인. 디스크 종류와 설치 후 여유 공간은 미확인. WSL 2 실제 실행은 확인 완료.
- PC 2 Ubuntu 설치·WSL2 실행: 아직 미완료.
- PC 2 예전 ai120 커널은 깨진 연결이므로 새 D 커널 선택 필요.
- GUI 전체 동작·개별 과거 프로젝트는 별도 실행 검증 필요.
- PC 2의 D에는 공식 설치 파일과 실패한 설치의 보관 폴더가 남아 있다. C 공간에는 영향을 주지 않으며 이번에 삭제했다고 기록하지 않는다.
- Docker, AWS, Kubernetes는 각각 계획표 9·17·21주차에 준비한다. AWS 예산은 미정이다.

## 다음 Codex에게 전달할 문장

> 이 저장소의 docs/handoff.md, docs/environments.md, daily/2026-09-18.md를 읽고 이어서 진행해줘. 지금은 PC 1이야. PC 1은 Ubuntu 26.04.1 LTS를 설치했고 jaeho 계정과 WSL 2 Running 상태까지 확인했어. PC 2는 Anaconda 이전을 마쳤지만 Ubuntu는 아직 미설치야. 다음은 PC 1의 Ubuntu 업데이트와 기본 명령 실습이야. 한 번에 한 단계씩 진행하고 기록을 남겨줘. push는 내가 직접 할게. 기존 환경은 확인 없이 삭제하지 말아줘.

## 반드시 유지할 설명 방식

루트 [AGENTS.md](../AGENTS.md)를 따른다. 모든 터미널 명령은 실행 환경·목적·옵션·예상 결과·변경 영향을 설명하고 주석을 붙인다. 한 번에 한 단계씩 진행한다. 새 대화에서도 이 파일과 AGENTS.md를 먼저 읽도록 요청한다.

현재 다음 단계는 Windows 저장소의 기록을 사용자가 push한 뒤 Ubuntu 학습 작업 폴더를 준비하는 것이다. VS Code 연결 성공을 저장소 clone 완료나 패키지 업데이트 완료로 해석하지 않는다.

## 최신 재개 지점 — 2026-09-18 수업 종료

이 절은 앞선 다음 단계 안내보다 최신이다. 루트 AGENTS.md와 daily/2026-09-18.md의 마지막 기록을 먼저 읽는다.

- 현재 작업 사본: PC 1 Ubuntu의 /home/jaeho/ai-quant-learning. Windows 사본을 병행 수정하지 않는다.
- Ubuntu와 VS Code 연결, Git 소스 제어 사용, 자동 저장 설정까지 진행했다.
- curl 8.18.0과 예제 사이트 HTML 요청 성공 확인. 시간 제약으로 추가 curl 실습은 중단하고 1주차 5일차 이후로 이월했다.
- 다음 작업: edumgt 참고 저장소 복제 상태 확인 후 필요한 7개만 보관. python-crawling-lab, docker-class, edumgt-lab-init, investment-analysis, domain-rag-lab, aws-ec2-alb-lab, lumina-invest.
- 54개 전체를 복제하는 이전 스크립트는 사용하지 않는다. 실행됐는지 미확인이므로 기존 폴더부터 읽기 전용으로 확인한다.
- 이후 Ubuntu 패키지 업데이트 등 환경 준비를 진행한다. curl 상세 실습으로 먼저 넘어가지 않는다.
- 재개할 때 git 상태와 동기화 상태를 확인한다. 기록 업로드는 사용자가 직접 한다.

## 최신 재개 지점 — 2026-09-21

이 절은 앞선 재개 안내보다 최신이다.

- PC 1의 Ubuntu에서 에듀엠지티 참고 저장소 7개 복제를 완료했다.
- 저장 위치: /home/jaeho/references/edumgt
- 저장소 목록과 받은 커밋 번호는 daily/2026-09-21.md에 기록했다.
- 참고 저장소를 다시 복제할 필요는 없다.
- 참고 프로젝트의 코드 실행과 의존성 설치는 아직 하지 않았다.
- 다음은 Ubuntu 패키지 업데이트 상태 확인과 환경 준비다.
- curl 상세 실습은 1주차 5일차 이후에 진행한다.
- AGENTS.md에 따라 모든 명령을 설명하고 한 단계씩 안내한다.

## 최신 재개 지점 — 2026-09-21 업데이트 확인 후

- 참고 저장소 7개 복제를 완료했다.
- PC 1의 Ubuntu 패키지 업그레이드를 진행했다.
- dpkg --audit에서 미완료 패키지가 보고되지 않았다.
- PID 1은 systemd, 시스템 상태는 running으로 확인했다.
- 다음은 계획표 1주차 3일차의 기본 파일·폴더 명령 실습이다.
- curl 상세 실습은 예정된 진도에서 진행한다.

## 최신 재개 지점 — 1주차 3일차 완료

- PC 1 Ubuntu에서 계획표 3일차 기본 파일·폴더 명령 실습을 완료했다.
- 실습 결과물은 exercises/linux-day03에 있다.
- 상세 기록은 daily/2026-09-21.md에 있다.
- 다음은 계획표 1주차 4일차: Git 설정 확인과 Python 가상환경 준비다.
- AGENTS.md에 따라 명령을 설명하고 한 단계씩 진행한다.

## 최신 재개 지점 — 1주차 4일차 완료

- PC 1 Ubuntu의 학습 저장소에 Python 3.14.4 가상환경을 만들었다.
- 위치: /home/jaeho/ai-quant-learning/.venv
- 활성화, Python·pip 경로, Git 추적 제외를 확인했다.
- 다음은 계획표 1주차 5일차: HTTP·HTML·JSON 기초와 요청 실습이다.
- 모든 명령을 설명하고 한 단계씩 진행한다.

## 최신 재개 지점 — 1주차 5일차 실습 후

- curl로 HTML·응답 헤더·JSON 조회와 JSON 파일 저장을 실습했다.
- 개인 프로필 원본 JSON은 Git 제외 규칙을 적용해 로컬에 보관한다.
- 다음에는 5일차 완료 기준인 응답 상태·본문 저장을 함께 확인한 뒤,
  6일차 BeautifulSoup 제목·링크 추출 실습으로 이어간다.

  ## 최신 재개 지점 — 1주차 5일차 완료

- HTTP·HTML·JSON 기초와 요청·응답 파일 저장 확인을 완료했다.
- 실습 파일: exercises/http-day05/example-headers.txt, example.html.
- 개인 프로필 JSON의 Git 제외 규칙은 유지한다.
- 다음은 1주차 6일차: BeautifulSoup으로 제목·링크를 추출하고
  pandas로 CSV를 만드는 실습이다.