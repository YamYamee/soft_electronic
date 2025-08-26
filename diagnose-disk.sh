#!/bin/bash

echo "🔍 디스크 공간 진단 중..."

echo "=== 전체 디스크 사용량 ==="
df -h

echo ""
echo "=== 디렉토리별 사용량 (상위 10개) ==="
sudo du -sh /* 2>/dev/null | sort -h | tail -10

echo ""
echo "=== Docker 관련 사용량 ==="
if command -v docker &> /dev/null; then
    echo "Docker 시스템 사용량:"
    docker system df 2>/dev/null || echo "Docker 시스템 정보 확인 불가"
    
    echo ""
    echo "Docker 디렉토리 사용량:"
    sudo du -sh /var/lib/docker/* 2>/dev/null | sort -h | tail -5
else
    echo "Docker가 설치되지 않음"
fi

echo ""
echo "=== 큰 파일들 (100MB 이상) ==="
sudo find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null | head -10

echo ""
echo "=== 로그 파일 사용량 ==="
sudo du -sh /var/log/* 2>/dev/null | sort -h | tail -5

echo ""
echo "=== APT 캐시 사용량 ==="
sudo du -sh /var/cache/apt/archives/ 2>/dev/null

echo ""
echo "=== 임시 파일 사용량 ==="
sudo du -sh /tmp /var/tmp 2>/dev/null

echo ""
echo "=== 스냅 패키지 사용량 ==="
if command -v snap &> /dev/null; then
    sudo du -sh /var/lib/snapd/snaps/ 2>/dev/null || echo "스냅 사용량 확인 불가"
    snap list --all | grep disabled | wc -l | xargs echo "비활성 스냅 패키지 수:"
else
    echo "Snap 패키지 없음"
fi

echo ""
echo "🎯 추천 정리 방법:"
echo "1. Docker 정리: docker system prune -af --volumes"
echo "2. APT 정리: sudo apt autoremove && sudo apt autoclean"
echo "3. 로그 정리: sudo journalctl --vacuum-time=3d"
echo "4. 임시 파일: sudo rm -rf /tmp/* /var/tmp/*"
echo "5. 스냅 정리: 비활성 패키지 제거"
