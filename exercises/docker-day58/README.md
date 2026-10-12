# 9주차 58일차 — 이미지·컨테이너·포트·볼륨

실습 날짜: 2026-10-12. 57일차에 연결한 Docker Desktop으로 작은 웹 서버를 실행하고, 컨테이너를 삭제해도 볼륨의 파일이 남는지 확인했다.

## 개념과 실습 흐름

| 개념 | 쉬운 설명 | 이번 예제 |
| --- | --- | --- |
| Docker | 이미지를 이용해 컨테이너를 만들고 실행·관리하는 도구 | Ubuntu 명령 → Docker Desktop 엔진 |
| 이미지 | 프로그램과 실행에 필요한 파일을 묶은 것 | nginx:stable-alpine |
| 컨테이너 | 이미지로 만든 프로그램 실행 공간. 중지된 상태로도 남는다. | web-day58 |
| Nginx | 웹 요청을 받아 응답을 보내는 프로그램 | 브라우저에 기본 페이지 전달 |
| 포트 연결 | 내 컴퓨터의 접속 입구를 컨테이너의 입구에 연결 | 127.0.0.1:8080 → 컨테이너 80 |
| 볼륨 | 컨테이너와 별도로 보관하는 저장 공간 | day58-data |

웹 요청: 브라우저 → localhost:8080 → 컨테이너의 80번 포트 → Nginx 응답 → 브라우저가 화면 표시.

파일 보관: 저장용 컨테이너 → /data/message.txt → day58-data 볼륨 → 저장용 컨테이너 삭제 → 새 조회용 컨테이너에서 같은 파일 읽기.

## 실행 환경과 연결 확인

명령은 Ubuntu 터미널에서 실행한다. Docker Desktop이 실행 중이고 설정의 Resources → WSL integration에서 Ubuntu가 켜져 있어야 한다. 작업 폴더와 Python 가상환경에 관계없이 Docker 명령을 사용할 수 있다.

```bash
# 읽기 전용으로 명령 도구와 서버의 연결을 확인합니다.
docker version

# 읽기 전용으로 현재 연결된 엔진 이름과 운영체제를 확인합니다.
docker info --format '엔진 이름: {{.Name}} / 운영체제: {{.OperatingSystem}}'
```

실제 결과는 Server가 Docker Desktop 4.94.0, 엔진 이름이 docker-desktop이었다. 처음에는 WSL 통합 안내와 함께 docker 명령을 사용할 수 없었으나 연결 복구 후 정상 출력됐다.

## 기존 컨테이너 다시 실행

```bash
# -a로 종료된 컨테이너도 표시하고 정확한 이름으로 조회합니다.
docker ps -a --filter 'name=^/hello-desktop$'

# 기존 컨테이너를 다시 시작하고 -a로 출력을 터미널에 연결합니다.
docker start -a hello-desktop

# 다시 실행한 뒤 ID와 종료 상태를 읽기 전용으로 확인합니다.
docker ps -a --filter 'name=^/hello-desktop$'
```

실행 전후 ID는 a9528a9d6994로 같았고 Exited (0), 즉 정상 종료였다. hello-world는 안내문을 출력하고 끝나는 프로그램이다. 안내문 속 이미지 다운로드·컨테이너 생성 설명은 고정 문구이며, start 때 새 컨테이너를 만들었다는 뜻은 아니다.

## Nginx 웹 서버

다음 run 명령은 최초 실습 기록이다. 현재 web-day58이 남아 있으므로 같은 이름으로 반복 실행하지 않는다. 다시 보고 싶으면 아래 start를 사용한다.

```bash
# 새 컨테이너를 만들고 -d로 백그라운드 실행합니다. -p로 로컬 8080과 컨테이너 80을 연결합니다.
docker run -d --name web-day58 -p 127.0.0.1:8080:80 nginx:stable-alpine

# 실행 중인 컨테이너의 상태와 포트 연결을 조회합니다.
docker ps --filter 'name=^/web-day58$'

# 웹 서버를 중지합니다. 컨테이너 자체는 남습니다.
docker stop web-day58

# 중지된 상태까지 포함해 확인합니다.
docker ps -a --filter 'name=^/web-day58$'

# 같은 컨테이너를 다시 시작합니다.
docker start web-day58
```

브라우저에서 http://localhost:8080/ 에 접속해 최초 실행과 재시작 후 모두 Nginx 기본 페이지를 확인했다. ID fd403de064b2는 중지·재시작 전후 같았고, 포트는 127.0.0.1:8080->80/tcp였다. 중지 직후 브라우저 접속 실패까지 확인한 기록은 없다.

## 컨테이너 삭제 후 볼륨 파일 읽기

아래는 완료한 실습 기록이며, 보관 중인 조회용 컨테이너와 이름이 겹치므로 전체를 그대로 재실행하지 않는다. 파일 쓰기 명령은 같은 파일이 있으면 덮어쓴다.

```bash
# 컨테이너와 별도로 유지되는 이름 있는 볼륨을 만듭니다.
docker volume create day58-data

# 볼륨을 /data에 연결하고 파일을 저장한 뒤 내용을 출력합니다.
docker run --name volume-write-day58 \
    --mount type=volume,source=day58-data,target=/data \
    nginx:stable-alpine \
    sh -c 'printf "%s\n" "day58 volume data" > /data/message.txt && cat /data/message.txt'

# 종료된 저장용 컨테이너만 삭제합니다. 이름 있는 볼륨은 남습니다.
docker rm volume-write-day58

# 새 컨테이너에 같은 볼륨을 읽기 전용으로 연결하고 파일을 출력합니다.
docker run --name volume-read-day58 \
    --mount type=volume,source=day58-data,target=/data,readonly \
    nginx:stable-alpine cat /data/message.txt
```

저장할 때와 저장용 컨테이너 삭제 후 모두 `day58 volume data`가 출력됐다. 이 두 컨테이너는 nginx 이미지를 사용하지만, 실행할 명령을 sh 또는 cat으로 지정했으므로 웹 서버를 켜는 실습이 아니다. readonly 연결은 사용했으나 쓰기를 시도해 거부되는지는 별도로 검사하지 않았다.

## 마무리 상태와 다음 학습

- web-day58을 중지했다. hello-desktop과 volume-read-day58도 정상 종료 상태다.
- day58-data 볼륨, 이미지, 위 세 컨테이너는 보관한다. 저장용 volume-write-day58은 삭제했다.
- 실습을 따라 실행하고 개념을 반복 설명한 뒤, 사용자는 Docker 실행·Nginx 실행·컨테이너와 볼륨의 분리 확인이라는 흐름을 요약했다. 독립적으로 명령을 작성하는 숙련도는 별도 연습 대상이다.
- 다음 59일차에는 분석 앱의 Dockerfile과 .dockerignore를 작성한다. 56일차 API가 52일차 코드를 가져오는 구조와 DB 경로부터 확인한다.
- Docker의 볼륨·이미지는 Git 커밋에 포함되지 않는다. 이번에는 설명 문서를 저장한다.

참고: [Docker WSL 안내](https://docs.docker.com/desktop/features/wsl/), [컨테이너 실행](https://docs.docker.com/engine/containers/run/), [볼륨](https://docs.docker.com/engine/storage/volumes/).
