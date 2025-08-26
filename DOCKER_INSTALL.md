# 🐳 서버에 Docker 설치하기

## 방법 1: 스크립트 실행 (권장)

```bash
# 스크립트 실행 권한 부여 후 실행
chmod +x install-docker.sh
./install-docker.sh
```

## 방법 2: 원라이너 (빠른 설치)

```bash
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && sudo usermod -aG docker $USER && sudo systemctl enable docker && sudo systemctl start docker
```

## 방법 3: 단계별 수동 설치

```bash
# 1. 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 2. 필수 패키지 설치
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# 3. Docker GPG 키 추가
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# 4. Docker 저장소 추가
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# 5. Docker 설치
sudo apt update && sudo apt install -y docker-ce

# 6. Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 7. 사용자 권한 설정
sudo usermod -aG docker $USER

# 8. 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker
```

## 설치 후 확인

```bash
# 터미널 재시작 후 또는
newgrp docker

# 버전 확인
docker --version
docker-compose --version

# 테스트 실행
docker run hello-world
```

## GitHub Actions Runner 사용자 설정

```bash
# Actions runner 사용자도 docker 그룹에 추가
sudo usermod -aG docker actions-runner
# 또는 실제 runner 사용자명으로 변경

# Runner 서비스 재시작
sudo systemctl restart actions.runner.*
```

## 트러블슈팅

```bash
# Docker 데몬 상태 확인
sudo systemctl status docker

# Docker 데몬 재시작
sudo systemctl restart docker

# 권한 문제 해결
sudo chmod 666 /var/run/docker.sock
```
