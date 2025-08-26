#!/bin/bash

echo "🧹 서버 디스크 정리 시작..."

# 현재 디스크 사용량 확인
echo "=== 현재 디스크 사용량 ==="
df -h

echo ""
echo "=== Docker 정리 시작 ==="

# Docker 시스템 정리
echo "1. 사용하지 않는 Docker 이미지 정리..."
docker image prune -af

echo "2. 사용하지 않는 Docker 컨테이너 정리..."
docker container prune -f

echo "3. 사용하지 않는 Docker 볼륨 정리..."
docker volume prune -f

echo "4. 사용하지 않는 Docker 네트워크 정리..."
docker network prune -f

echo "5. Docker 빌드 캐시 정리..."
docker builder prune -af

echo "6. Docker 전체 시스템 정리..."
docker system prune -af --volumes

echo ""
echo "=== 시스템 정리 ==="

# APT 캐시 정리
echo "7. APT 캐시 정리..."
sudo apt autoremove -y
sudo apt autoclean
sudo apt clean

# 로그 파일 정리
echo "8. 로그 파일 정리..."
sudo journalctl --vacuum-time=3d
sudo find /var/log -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true

# 임시 파일 정리
echo "9. 임시 파일 정리..."
sudo rm -rf /tmp/*
sudo rm -rf /var/tmp/*

# 스냅 패키지 정리 (Ubuntu)
echo "10. 스냅 패키지 정리..."
sudo snap list --all | awk '/disabled/{print $1, $3}' | while read snapname revision; do
    sudo snap remove "$snapname" --revision="$revision" 2>/dev/null || true
done

echo ""
echo "=== 정리 완료 ==="
df -h

echo ""
echo "🎯 Docker 이미지 크기 줄이기 팁:"
echo "1. .dockerignore 파일 확인"
echo "2. 불필요한 파일 제외"
echo "3. 멀티스테이지 빌드 사용"

# 사용 가능한 공간 확인
available_space=$(df / | awk 'NR==2 {print $4}')
if [ $available_space -lt 1000000 ]; then
    echo "⚠️  경고: 여전히 디스크 공간이 부족합니다 (1GB 미만)"
    echo "추가 정리가 필요할 수 있습니다."
else
    echo "✅ 충분한 디스크 공간이 확보되었습니다!"
fi
