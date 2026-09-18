# 한국 주식 AI 퀀트 학습 기록

Ubuntu에서 시작해 크롤링, 백테스트, AI 에이전트, Docker, AWS, Kubernetes를 직접 실습하는 개인 학습 저장소입니다.

## 학습 방식
평일 3시간, 주말 4시간을 기준으로 진행합니다. 이해한 내용과 실제 실행한 결과를 기록하고, 실패한 시도도 남깁니다.

- [학습 도우미와 명령어 설명 원칙](AGENTS.md)
- [24주 일별 계획](docs/learning-plan.md)
- [일일 기록 양식](templates/daily-log.md)
- [첫 준비 기록](daily/2026-09-17.md)
- [Git과 두 컴퓨터 사용 방법](docs/workflow.md)
- [최신 인수인계 — 다른 컴퓨터에서 여기부터](docs/handoff.md)
- [두 컴퓨터 환경표](docs/environments.md)
- [PC 2 정리·Anaconda 이전 완료 기록](daily/2026-09-18.md)

## 현재 진행 상태 — 2026-09-18

PC 2는 환경 정리와 Anaconda D 이전을 마쳤고 Ubuntu는 미설치입니다. PC 1은 Ubuntu 26.04.1 LTS 설치, jaeho 계정 생성, WSL 2 실행과 VS Code의 WSL 연결을 확인했습니다. VS Code 터미널에서 whoami 결과 jaeho, pwd 결과 /home/jaeho를 사용자 화면으로 확인했습니다. 다음은 기록 업로드와 Ubuntu 작업 폴더 준비입니다. 패키지 업데이트는 아직 미확인입니다. 자세한 재개 순서는 [인수인계](docs/handoff.md)에 있습니다.

## 폴더
- daily/: 날짜별 학습 기록
- exercises/: 직접 작성한 실습 코드
- docs/: 계획과 사용 방법
- templates/: 기록 양식
- scripts/: 저장 보조 도구
- data/: 로컬 데이터. Git 업로드 제외

## 저장
PowerShell에서 저장소 폴더를 열고 실행합니다.

```powershell
./scripts/save-learning.ps1
```

로컬 커밋만 저장합니다. 이후 사용자가 직접 다음 명령으로 GitHub에 업로드합니다.

```powershell
git push
```

이 스크립트는 상시 실행되는 예약 작업이 아닙니다. 자동 커밋 예약은 아직 설정하지 않았습니다. 선택 기능인 -Push는 자동 설정에 사용하지 않습니다.
원문 금융 데이터·비밀키·계좌 정보는 올리지 않습니다.
