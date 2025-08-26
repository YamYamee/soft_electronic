#!/bin/bash

# GitHub Actions Self-hosted Runner 설정 스크립트

set -e

echo "🚀 GitHub Actions Self-hosted Runner 설정을 시작합니다..."

# 환경 변수 확인
if [[ -z "$GITHUB_TOKEN" ]]; then
    echo "❌ GITHUB_TOKEN 환경변수가 설정되지 않았습니다."
    echo "GitHub Personal Access Token을 설정해주세요."
    exit 1
fi

if [[ -z "$GITHUB_REPO" ]]; then
    echo "❌ GITHUB_REPO 환경변수가 설정되지 않았습니다."
    echo "예: export GITHUB_REPO='YamYamee/soft_electronic'"
    exit 1
fi

# 시스템 업데이트
echo "📦 시스템 패키지 업데이트..."
sudo apt-get update
sudo apt-get upgrade -y

# 필수 패키지 설치
echo "🔧 필수 패키지 설치..."
sudo apt-get install -y \
    curl \
    wget \
    git \
    unzip \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    jq \
    docker.io \
    docker-compose \
    python3 \
    python3-pip \
    nodejs \
    npm

# Docker 권한 설정
echo "🐳 Docker 권한 설정..."
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker

# 런너 사용자 생성
echo "👤 GitHub Actions 런너 사용자 생성..."
sudo useradd -m -s /bin/bash github-runner || true
sudo usermod -aG docker github-runner

# 런너 디렉토리 생성
RUNNER_HOME="/home/github-runner"
sudo mkdir -p $RUNNER_HOME/actions-runner
sudo chown -R github-runner:github-runner $RUNNER_HOME

# 런너 다운로드 및 설치
echo "⬇️ GitHub Actions Runner 다운로드..."
cd $RUNNER_HOME/actions-runner

# 최신 버전 확인
RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r '.tag_name' | sed 's/v//')
echo "📋 Runner 버전: $RUNNER_VERSION"

# 런너 다운로드
sudo -u github-runner wget -O actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz \
    https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# 압축 해제
sudo -u github-runner tar xzf actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# 등록 토큰 가져오기
echo "🔑 GitHub Repository 등록 토큰 가져오기..."
REGISTRATION_TOKEN=$(curl -s -X POST \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    https://api.github.com/repos/$GITHUB_REPO/actions/runners/registration-token | jq -r '.token')

if [[ "$REGISTRATION_TOKEN" == "null" ]]; then
    echo "❌ 등록 토큰을 가져오는데 실패했습니다."
    echo "GitHub Token의 권한을 확인해주세요."
    exit 1
fi

# 런너 설정
echo "⚙️ GitHub Actions Runner 설정..."
sudo -u github-runner ./config.sh \
    --url https://github.com/$GITHUB_REPO \
    --token $REGISTRATION_TOKEN \
    --name "self-hosted-posture-classifier" \
    --labels "self-hosted,runner,linux,x64,posture-classifier" \
    --work _work \
    --replace

# 서비스 설치
echo "🎯 Runner 서비스 설치..."
sudo ./svc.sh install github-runner
sudo ./svc.sh start

# 환경 설정 파일 생성
echo "📝 환경 설정 파일 생성..."
sudo -u github-runner tee $RUNNER_HOME/.env << EOF
# GitHub Actions Runner 환경 변수
RUNNER_HOME=$RUNNER_HOME
GITHUB_REPO=$GITHUB_REPO
DOCKER_BUILDKIT=1
COMPOSE_DOCKER_CLI_BUILD=1

# 자세 분류 시스템 환경 변수
DATABASE_URL=postgresql://posture_user:posture_password123@localhost:5432/posture_classification
REDIS_URL=redis://localhost:6379/0
ENVIRONMENT=production
LOG_LEVEL=INFO
EOF

# Python 의존성 설치
echo "🐍 Python 의존성 사전 설치..."
sudo -u github-runner pip3 install \
    fastapi \
    uvicorn \
    websockets \
    scikit-learn \
    pandas \
    numpy \
    pytest \
    black \
    isort \
    flake8

# Node.js 도구 설치
echo "📦 Node.js 도구 설치..."
sudo npm install -g pm2

# 로그 디렉토리 생성
sudo mkdir -p /var/log/github-runner
sudo chown github-runner:github-runner /var/log/github-runner

# 로그 로테이션 설정
sudo tee /etc/logrotate.d/github-runner << EOF
/var/log/github-runner/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    copytruncate
    create 644 github-runner github-runner
}
EOF

# 모니터링 스크립트 생성
sudo tee /usr/local/bin/runner-monitor.sh << 'EOF'
#!/bin/bash

# GitHub Actions Runner 모니터링 스크립트

RUNNER_HOME="/home/github-runner"
LOG_FILE="/var/log/github-runner/monitor.log"

# 런너 상태 확인
check_runner_status() {
    local status=$(sudo systemctl is-active actions.runner.*)
    echo "$(date): Runner Status: $status" >> $LOG_FILE
    
    if [[ "$status" != "active" ]]; then
        echo "$(date): Runner가 비활성 상태입니다. 재시작을 시도합니다." >> $LOG_FILE
        sudo systemctl restart actions.runner.*
        sleep 10
        
        local new_status=$(sudo systemctl is-active actions.runner.*)
        echo "$(date): 재시작 후 Status: $new_status" >> $LOG_FILE
        
        if [[ "$new_status" != "active" ]]; then
            echo "$(date): ❌ Runner 재시작 실패" >> $LOG_FILE
        else
            echo "$(date): ✅ Runner 재시작 성공" >> $LOG_FILE
        fi
    fi
}

# 디스크 용량 확인
check_disk_space() {
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    echo "$(date): Disk Usage: ${disk_usage}%" >> $LOG_FILE
    
    if [[ $disk_usage -gt 80 ]]; then
        echo "$(date): ⚠️ 디스크 용량 부족: ${disk_usage}%" >> $LOG_FILE
        # Docker 이미지 정리
        docker system prune -f
        echo "$(date): Docker 이미지 정리 완료" >> $LOG_FILE
    fi
}

# 메모리 사용량 확인
check_memory() {
    local memory_usage=$(free | awk 'NR==2{printf "%.1f", $3*100/($3+$4)}')
    echo "$(date): Memory Usage: ${memory_usage}%" >> $LOG_FILE
    
    if (( $(echo "$memory_usage > 90" | bc -l) )); then
        echo "$(date): ⚠️ 메모리 사용량 높음: ${memory_usage}%" >> $LOG_FILE
    fi
}

# 모니터링 실행
check_runner_status
check_disk_space
check_memory

echo "$(date): 모니터링 체크 완료" >> $LOG_FILE
EOF

sudo chmod +x /usr/local/bin/runner-monitor.sh

# 크론탭 설정 (5분마다 모니터링)
echo "⏰ 크론탭 모니터링 설정..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/runner-monitor.sh") | crontab -

# 방화벽 설정
echo "🔥 방화벽 설정..."
sudo ufw allow ssh
sudo ufw allow 8000/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# 설정 완료 확인
echo "✅ GitHub Actions Self-hosted Runner 설정 완료!"
echo ""
echo "📋 설정 정보:"
echo "  - Runner 이름: self-hosted-posture-classifier"
echo "  - Labels: self-hosted, runner, linux, x64, posture-classifier"
echo "  - 홈 디렉토리: $RUNNER_HOME"
echo "  - 로그 디렉토리: /var/log/github-runner"
echo ""
echo "🔍 상태 확인:"
sudo systemctl status actions.runner.* --no-pager

echo ""
echo "📝 다음 단계:"
echo "1. GitHub Repository Settings > Actions > Runners에서 런너 확인"
echo "2. .github/workflows/ci-cd.yml 파일의 secrets 설정"
echo "3. 첫 번째 배포 테스트 실행"
echo ""
echo "🚀 준비 완료! GitHub Actions workflow를 실행할 수 있습니다."
