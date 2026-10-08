# 9주차 57일차 — WSL Ubuntu에 Docker Engine 설치

## 목적

분석 API를 컨테이너로 실행하기 위한 Docker 환경을 준비한다.

## 환경과 설치 방식

- Windows 10, WSL 3.0.1, Ubuntu 배포판은 WSL 2로 실행.
- Ubuntu 26.04.1 LTS, x86_64, systemd 실행 확인.
- 확인 당시 Windows C 드라이브 여유 공간 약 105GB.
- 확인한 두 일반 설치 경로에 Docker Desktop이 없었고 실행 프로세스도 없었다.
- Ubuntu의 Docker 관련 패키지와 공식 저장소 등록이 없음을 확인했다.
- Docker Desktop 대신 WSL Ubuntu 내부에 Docker Engine을 설치했다.
- Python 가상환경과 별개의 시스템 설치이며 기존 가상환경은 유지했다.

## 설치 과정

1. Ubuntu 패키지 목록을 갱신했다.
2. ca-certificates와 curl이 최신 상태임을 확인했다.
3. Docker 공식 서명 키와 APT 저장소를 등록했다.
4. resolute·amd64용 Docker 패키지 목록을 정상적으로 받았다.
5. docker-ce, docker-ce-cli, containerd.io,
   docker-buildx-plugin, docker-compose-plugin을 설치했다.
6. Docker 서비스 시작과 클라이언트·서버 연결을 확인했다.

## 실제 확인한 버전

| 항목 | 버전 |
|---|---|
| Docker Client·Server | 29.8.2 |
| containerd | 2.3.6 |
| runc | 1.5.1 |
| Buildx | 0.37.1 |
| Compose | 5.6.0 |

## 실행 확인

Ubuntu 터미널에서 다음 명령을 실행했다.

```bash
# 명령 도구와 Docker 엔진의 버전·연결 상태를 조회합니다.
sudo docker version

# 빌드 플러그인의 버전을 조회합니다.
docker buildx version

# Compose 플러그인의 버전을 조회합니다.
docker compose version

# 시험용 컨테이너를 실행하고 종료 후 해당 컨테이너를 제거합니다.
sudo docker run --rm hello-world
```

- Client와 Server가 모두 표시됐다.
- hello-world 이미지가 로컬에 없어 Docker Hub에서 내려받았다.
- Hello from Docker! 출력으로 컨테이너 실행 성공을 확인했다.
- --rm은 종료된 컨테이너를 제거하고 이미지는 남긴다.
- 현재 엔진 접근 명령은 sudo로 실행한다.
- docker 그룹에 사용자를 추가하는 설정은 하지 않았다.

## 문제와 해결

- Windows용 wsl·PowerShell 명령을 Ubuntu에서 실행해 명령 없음 오류가 났다.
- Windows PowerShell에서 다시 실행해 WSL 상태를 확인했다.
- Ubuntu에서 제안된 apt install wsl은 실행하지 않았다.
- 이미지가 로컬에 없다는 안내는 실패가 아니라 다운로드 전 안내였다.

## 범위와 다음 단계

- Docker 설치와 시험용 컨테이너 실행까지 확인했다.
- 분석 앱의 이미지 빌드와 컨테이너 실행은 아직 하지 않았다.
- 다음은 58일차: 이미지·컨테이너·포트·볼륨의 역할을 작은 예제로 확인한다.

## 참고 자료

- https://github.com/edumgt/docker-class/tree/50547fd32243d7a79a23c1f779604ad73030aff5/docker-basics/02-Docker-Installation
- https://github.com/edumgt/edumgt-lab-init
- https://docs.docker.com/engine/install/ubuntu/

참고 저장소의 여러 환경별 예제를 그대로 실행하지 않고,
현재 WSL Ubuntu 환경에 맞춰 Docker 공식 설치 절차를 적용했다.

## VS Code에서 이미지·컨테이너·로그 확인

- Microsoft Docker 확장 묶음의 Container Tools를 WSL Ubuntu에서 사용했다.
- 처음에는 Docker 엔진 접근 권한 부족으로 permission denied가 표시됐다.
- jaeho를 docker 그룹에 추가하고 Ubuntu와 VS Code 연결을 다시 시작했다.
- sudo 없이 docker version의 Client·Server 연결을 확인했다.
- VS Code Images 목록에서 hello-world 이미지를 확인했다.
- docker run --name hello-vscode hello-world로 컨테이너를 실행했다.
- --rm을 생략했으므로 종료된 hello-vscode 컨테이너가 남았다.
- VS Code Containers 목록과 View Logs에서 실행 기록을 확인했다.
- Docker Desktop을 추가 설치하지 않고 기존 Ubuntu Engine에 연결했다.
- docker 그룹은 Docker를 통한 관리자 수준의 작업 권한을 부여한다.

