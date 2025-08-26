# 🚀 자세 분류 시스템 배포 가이드

## 📋 목차

1. [사전 준비](#사전-준비)
2. [Self-hosted Runner 설정](#self-hosted-runner-설정)
3. [GitHub Secrets 설정](#github-secrets-설정)
4. [로컬 개발 환경](#로컬-개발-환경)
5. [CI/CD 파이프라인](#cicd-파이프라인)
6. [모니터링 및 운영](#모니터링-및-운영)
7. [트러블슈팅](#트러블슈팅)

## 🔧 사전 준비

### 필수 소프트웨어

- **Docker & Docker Compose**: 컨테이너 실행 환경
- **Git**: 소스코드 관리
- **Python 3.13+**: 개발 환경
- **PostgreSQL**: 데이터베이스 (Docker로 실행)
- **Redis**: 캐시 및 세션 관리 (Docker로 실행)

### 시스템 요구사항

- **CPU**: 최소 2코어, 권장 4코어
- **RAM**: 최소 4GB, 권장 8GB
- **디스크**: 최소 20GB 여유 공간
- **네트워크**: 인터넷 연결 (GitHub, Docker Hub 접근)

## 🏃‍♂️ Self-hosted Runner 설정

### 1. 런너 서버 준비

```bash
# Ubuntu/Debian 기준
sudo apt-get update
sudo apt-get install -y curl wget git unzip

# 환경 변수 설정
export GITHUB_TOKEN="your_github_personal_access_token"
export GITHUB_REPO="YamYamee/soft_electronic"
```

### 2. 런너 설치 스크립트 실행

```bash
# 스크립트 실행 권한 부여
chmod +x setup-runner.sh

# 런너 설정 실행
./setup-runner.sh
```

### 3. 런너 상태 확인

```bash
# 런너 서비스 상태 확인
sudo systemctl status actions.runner.*

# 런너 로그 확인
sudo journalctl -u actions.runner.* -f
```

## 🔐 GitHub Secrets 설정

GitHub Repository > Settings > Secrets and variables > Actions에서 다음 secrets을 설정하세요:

### Production 환경

```
PROD_DATABASE_URL=postgresql://posture_prod_user:secure_password@localhost:5432/posture_classification_prod
PROD_REDIS_URL=redis://localhost:6379/0
POSTGRES_PROD_PASSWORD=secure_database_password
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

### Staging 환경

```
STAGING_DATABASE_URL=postgresql://posture_staging_user:staging_password@localhost:5433/posture_classification_staging
STAGING_REDIS_URL=redis://localhost:6380/0
```

## 💻 로컬 개발 환경

### 1. 저장소 클론

```bash
git clone https://github.com/YamYamee/soft_electronic.git
cd soft_electronic
```

### 2. Python 환경 설정

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\\Scripts\\activate     # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 3. 로컬 Docker 환경 실행

```bash
# 개발용 환경 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f posture_server
```

### 4. 테스트 실행

```bash
# 유닛 테스트
pytest tests/ -v

# 코드 품질 검사
black --check .
isort --check-only .
flake8 .
```

## 🔄 CI/CD 파이프라인

### 워크플로우 트리거

- **Push to main/master**: 프로덕션 배포
- **Push to develop**: 스테이징 배포
- **Pull Request**: 테스트 실행
- **Manual Dispatch**: 수동 배포

### 파이프라인 단계

1. **Test**: 코드 품질 검사, 유닛 테스트
2. **Security Scan**: 보안 취약점 스캔
3. **Build**: Docker 이미지 빌드 및 푸시
4. **Deploy Staging**: 스테이징 환경 배포
5. **Deploy Production**: 프로덕션 환경 배포 (Blue-Green)

### 배포 명령어

```bash
# 수동 배포 (스테이징)
gh workflow run ci-cd.yml -f environment=staging

# 수동 배포 (프로덕션)
gh workflow run ci-cd.yml -f environment=production
```

## 📊 모니터링 및 운영

### 대시보드 접속

- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Application**: http://localhost:8000

### 로그 위치

```bash
# 애플리케이션 로그
docker-compose logs posture_server

# 데이터베이스 로그
docker-compose logs postgres

# 시스템 로그
tail -f /var/log/github-runner/monitor.log
```

### 헬스체크 확인

```bash
# 서비스 상태 확인
curl http://localhost:8000/health

# 데이터베이스 연결 확인
docker exec posture_db psql -U posture_user -d posture_classification -c "SELECT 1;"
```

## 🛠 트러블슈팅

### 일반적인 문제

#### 1. Runner 연결 실패

```bash
# 런너 재등록
cd /home/github-runner/actions-runner
sudo -u github-runner ./config.sh remove
sudo -u github-runner ./config.sh --url https://github.com/YamYamee/soft_electronic --token NEW_TOKEN
```

#### 2. Docker 컨테이너 실행 실패

```bash
# 컨테이너 로그 확인
docker-compose logs posture_server

# 컨테이너 재시작
docker-compose restart posture_server

# 전체 스택 재시작
docker-compose down && docker-compose up -d
```

#### 3. 데이터베이스 연결 문제

```bash
# 데이터베이스 상태 확인
docker-compose ps postgres

# 데이터베이스 로그 확인
docker-compose logs postgres

# 데이터베이스 재시작
docker-compose restart postgres
```

#### 4. 메모리 부족

```bash
# 메모리 사용량 확인
free -h
docker stats

# Docker 정리
docker system prune -a -f
docker volume prune -f
```

### 성능 최적화

#### 1. Docker 이미지 최적화

```dockerfile
# Multi-stage build 사용
FROM python:3.13-slim as builder
# ... 빌드 단계

FROM python:3.13-slim as runtime
# ... 런타임 단계
```

#### 2. 데이터베이스 튜닝

```sql
-- PostgreSQL 성능 설정
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
SELECT pg_reload_conf();
```

## 📞 지원 및 문의

### 문제 보고

- **GitHub Issues**: https://github.com/YamYamee/soft_electronic/issues
- **Email**: support@yourcompany.com

### 문서 및 가이드

- **API 문서**: http://localhost:8000/docs
- **시스템 아키텍처**: docs/architecture.md
- **개발 가이드**: docs/development.md

---

## 🎯 배포 체크리스트

### 프로덕션 배포 전 확인사항

- [ ] 모든 테스트 통과
- [ ] 보안 스캔 통과
- [ ] 데이터베이스 백업 완료
- [ ] 스테이징 환경 검증 완료
- [ ] 모니터링 대시보드 설정
- [ ] 롤백 계획 준비
- [ ] 팀 공지 완료

### 배포 후 확인사항

- [ ] 헬스체크 정상
- [ ] 웹소켓 연결 테스트
- [ ] 예측 API 동작 확인
- [ ] 데이터베이스 연결 확인
- [ ] 로그 모니터링 정상
- [ ] 성능 메트릭 확인
- [ ] 알림 시스템 동작 확인

🚀 **배포 완료! 자세 분류 시스템이 성공적으로 운영 중입니다.**
