#!/bin/bash

echo "🐳 Docker Compose 설치 중..."

# 방법 1: Docker Compose Plugin (권장) - 이미 설치되어 있을 수 있음
echo "Docker Compose plugin 확인 중..."
if docker compose version &> /dev/null; then
    echo "✅ Docker Compose plugin이 이미 설치되어 있습니다!"
    docker compose version
    exit 0
fi

# 방법 2: Standalone Docker Compose 설치
echo "Standalone Docker Compose 설치 중..."

# 최신 버전 가져오기
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)

# Docker Compose 다운로드 및 설치
sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 실행 권한 부여
sudo chmod +x /usr/local/bin/docker-compose

# 심볼릭 링크 생성 (선택사항)
sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

echo "✅ Docker Compose 설치 완료!"
echo "버전 확인:"
docker-compose --version
docker compose version

echo ""
echo "🚀 이제 다음 명령어들을 사용할 수 있습니다:"
echo "   docker compose up -d      (새로운 방식, 권장)"
echo "   docker-compose up -d      (기존 방식)"
