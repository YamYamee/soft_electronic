#!/bin/bash

echo "🐳 Docker 설치 시작..."

# 시스템 업데이트
sudo apt-get update

# 필요한 패키지 설치
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Docker의 공식 GPG 키 추가
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Docker 저장소 추가
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 패키지 목록 업데이트
sudo apt-get update

# Docker Engine 설치
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Docker 서비스 시작 및 부팅시 자동 시작 설정
sudo systemctl start docker
sudo systemctl enable docker

# 현재 사용자를 docker 그룹에 추가 (sudo 없이 docker 명령 사용 가능)
sudo usermod -aG docker $USER

# Docker Compose 설치 (standalone)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

echo "✅ Docker 설치 완료!"
echo "📝 다음 명령어들로 설치 확인:"
echo "   docker --version"
echo "   docker-compose --version"
echo ""
echo "⚠️  중요: 터미널을 다시 시작하거나 다음 명령어를 실행하세요:"
echo "   newgrp docker"
echo ""
echo "🚀 이제 다음 명령어로 테스트해보세요:"
echo "   docker run hello-world"
