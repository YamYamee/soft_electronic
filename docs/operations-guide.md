# 📋 운영 가이드

## 개요

자세 분류 시스템의 일상적인 운영, 모니터링, 문제 해결을 위한 가이드입니다.

## 일일 운영 체크리스트

### 🌅 매일 아침 체크 (오전 9시)

- [ ] 시스템 상태 확인
  ```bash
  curl http://localhost:8000/health
  ```
- [ ] Grafana 대시보드 확인
  - 지난 24시간 트래픽
  - 에러율 체크
  - 응답시간 추이
- [ ] 로그 파일 확인
  ```bash
  tail -100 /var/log/posture_system/error.log
  ```
- [ ] 데이터베이스 백업 상태 확인
- [ ] 디스크 사용량 확인 (80% 이하 유지)

### 🌆 매일 저녁 체크 (오후 6시)

- [ ] 일일 통계 리포트 확인
- [ ] 예측 정확도 추이 분석
- [ ] 신규 에러 패턴 분석
- [ ] 자동 백업 성공 여부 확인

## 주간 운영 체크리스트

### 📊 매주 월요일

- [ ] 주간 성능 리포트 생성
- [ ] 모델 성능 지표 분석
- [ ] 사용자 피드백 검토
- [ ] 보안 패치 업데이트 확인

### 🔧 매주 금요일

- [ ] 시스템 백업 무결성 검증
- [ ] 로그 파일 아카이빙
- [ ] 성능 최적화 기회 검토
- [ ] 다음 주 계획 수립

## 모니터링 대시보드

### 🎯 핵심 KPI

| 지표          | 정상 범위 | 경고 임계값 | 위험 임계값 |
| ------------- | --------- | ----------- | ----------- |
| 응답 시간     | < 100ms   | 100-500ms   | > 500ms     |
| 에러율        | < 1%      | 1-5%        | > 5%        |
| CPU 사용률    | < 70%     | 70-85%      | > 85%       |
| 메모리 사용률 | < 80%     | 80-90%      | > 90%       |
| 디스크 사용률 | < 80%     | 80-90%      | > 90%       |
| 동시 연결 수  | < 1000    | 1000-2000   | > 2000      |

### 📈 Grafana 대시보드 구성

1. **시스템 개요**

   - 서비스 상태
   - 총 요청 수
   - 에러율 추이
   - 평균 응답 시간

2. **애플리케이션 메트릭**

   - WebSocket 연결 수
   - 예측 요청 수
   - 모델 정확도
   - 자세별 분포

3. **인프라 메트릭**
   - CPU/메모리/디스크 사용률
   - 네트워크 트래픽
   - 데이터베이스 성능
   - 컨테이너 상태

## 로그 관리

### 📝 로그 파일 위치

```
logs/
├── application/
│   ├── posture_classifier.log      # ML 모델 로그
│   ├── websocket_server.log        # 웹서버 로그
│   └── access.log                  # 접속 로그
├── system/
│   ├── nginx.log                   # Nginx 로그
│   ├── postgres.log                # 데이터베이스 로그
│   └── redis.log                   # Redis 로그
└── monitoring/
    ├── prometheus.log              # 메트릭 수집 로그
    └── grafana.log                 # 대시보드 로그
```

### 🔍 로그 분석 명령어

```bash
# 에러 로그 확인
grep -i error /var/log/posture_system/*.log

# 최근 1시간 활동 확인
find /var/log/posture_system -name "*.log" -newermt "1 hour ago" -exec tail -f {} \;

# 특정 사용자 활동 추적
grep "user_id:12345" /var/log/posture_system/access.log

# 응답 시간이 느린 요청 찾기
awk '$9 > 1000 {print $0}' /var/log/posture_system/access.log
```

### 📦 로그 로테이션 설정

```bash
# /etc/logrotate.d/posture-system
/var/log/posture_system/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    copytruncate
    create 644 www-data www-data
}
```

## 백업 및 복원

### 💾 자동 백업 스케줄

- **데이터베이스**: 매일 새벽 2시
- **모델 파일**: 매주 일요일 새벽 3시
- **설정 파일**: 매일 새벽 4시
- **로그 아카이브**: 매월 1일 새벽 5시

### 🗄️ 백업 스크립트

```bash
#!/bin/bash
# backup-database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/database"
DB_NAME="posture_classification"

# PostgreSQL 백업
docker exec posture_db pg_dump -U posture_user $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# 압축
gzip $BACKUP_DIR/db_backup_$DATE.sql

# 30일 이상 된 백업 파일 삭제
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Database backup completed: $DATE"
```

### 🔄 복원 절차

```bash
# 1. 서비스 중지
docker-compose down

# 2. 데이터베이스 복원
gunzip -c /backup/database/db_backup_20250827_020000.sql.gz | \
docker exec -i posture_db psql -U posture_user posture_classification

# 3. 모델 파일 복원
cp /backup/models/posture_model_v1.0.0.pkl ./posture_model.pkl

# 4. 서비스 재시작
docker-compose up -d

# 5. 헬스체크
sleep 30
curl http://localhost:8000/health
```

## 장애 대응

### 🚨 긴급 대응 절차

#### Level 1: 서비스 완전 중단

1. **즉시 대응** (5분 이내)

   ```bash
   # 서비스 상태 확인
   docker-compose ps

   # 빠른 재시작
   docker-compose restart posture_server
   ```

2. **원인 파악** (15분 이내)

   ```bash
   # 로그 확인
   docker-compose logs --tail=100 posture_server

   # 리소스 확인
   top
   df -h
   ```

3. **임시 복구** (30분 이내)
   - 이전 버전으로 롤백
   - 데이터베이스 백업 복원
   - 설정 파일 복원

#### Level 2: 성능 저하

1. **모니터링 확인**

   - Grafana 대시보드 분석
   - 응답 시간 추이 확인
   - 에러율 증가 원인 파악

2. **리소스 최적화**

   ```bash
   # 메모리 사용량 정리
   docker system prune -f

   # 데이터베이스 최적화
   docker exec posture_db psql -U posture_user -d posture_classification -c "VACUUM ANALYZE;"
   ```

#### Level 3: 부분 기능 장애

1. **기능별 격리**
   - 문제 구간 식별
   - 우회 방법 제공
   - 사용자 공지

### 📞 에스컬레이션 절차

| 시간       | 담당자      | 연락처        | 역할        |
| ---------- | ----------- | ------------- | ----------- |
| 0-30분     | 1차 대응팀  | Slack #alerts | 즉시 대응   |
| 30분-2시간 | 개발팀 리드 | 010-XXXX-XXXX | 기술적 해결 |
| 2시간+     | CTO         | 010-YYYY-YYYY | 의사결정    |

## 성능 최적화

### 🚀 시스템 튜닝

#### 데이터베이스 최적화

```sql
-- 인덱스 최적화
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_prediction_logs_created_at_posture
ON prediction_logs(created_at, predicted_posture);

-- 통계 정보 업데이트
ANALYZE prediction_logs;

-- 커넥션 풀 설정
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
SELECT pg_reload_conf();
```

#### 애플리케이션 튜닝

```python
# Redis 캐싱 활용
@lru_cache(maxsize=1000)
def get_cached_prediction(features_hash):
    return model.predict(features)

# 비동기 처리
async def process_batch_predictions(requests):
    tasks = [predict_async(req) for req in requests]
    return await asyncio.gather(*tasks)
```

#### 인프라 최적화

```yaml
# docker-compose.prod.yml
services:
  posture_server:
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 2G
        reservations:
          cpus: "1.0"
          memory: 1G
```

### 📊 성능 측정

```bash
# 부하 테스트
wrk -t12 -c400 -d30s --script=load_test.lua http://localhost:8000/

# 메모리 프로파일링
python -m memory_profiler websocket_server.py

# CPU 프로파일링
python -m cProfile -o profile.stats websocket_server.py
```

## 보안 관리

### 🔒 보안 체크리스트

#### 매일 확인

- [ ] 실패한 로그인 시도 확인
- [ ] 비정상적인 트래픽 패턴 감지
- [ ] SSL 인증서 만료일 확인

#### 매주 확인

- [ ] 보안 패치 업데이트
- [ ] 방화벽 규칙 검토
- [ ] 액세스 로그 분석

#### 매월 확인

- [ ] 보안 취약점 스캔
- [ ] 백업 암호화 상태 확인
- [ ] 사용자 권한 검토

### 🛡️ 보안 모니터링

```bash
# 실패한 인증 시도 확인
grep -i "authentication failed" /var/log/posture_system/*.log

# 비정상적인 IP 접근 확인
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr | head -20

# SSL 인증서 만료일 확인
openssl x509 -in /etc/ssl/certs/posture-system.crt -noout -dates
```

## 용량 계획

### 📈 성장 예측

| 항목              | 현재 | 6개월 후 | 1년 후 |
| ----------------- | ---- | -------- | ------ |
| 일일 요청 수      | 10K  | 100K     | 500K   |
| 데이터베이스 크기 | 1GB  | 10GB     | 50GB   |
| 동시 연결 수      | 100  | 1K       | 5K     |
| 서버 인스턴스     | 1    | 3        | 10     |

### 💾 스토리지 계획

```bash
# 현재 사용량 확인
df -h

# 데이터베이스 크기 확인
docker exec posture_db psql -U posture_user -d posture_classification -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# 로그 파일 크기 확인
du -sh /var/log/posture_system/*
```

## 업데이트 및 배포

### 🔄 정기 업데이트 스케줄

- **보안 패치**: 매주 화요일 오전 2시
- **마이너 업데이트**: 매월 첫째 주 화요일
- **메이저 업데이트**: 분기별 계획된 유지보수 시간

### 📋 배포 전 체크리스트

- [ ] 테스트 환경에서 검증 완료
- [ ] 백업 완료
- [ ] 롤백 계획 준비
- [ ] 사용자 공지 발송
- [ ] 모니터링 준비

### 🎯 배포 후 검증

```bash
# 헬스체크
curl http://localhost:8000/health

# 기능 테스트
curl -X POST http://localhost:8000/test-prediction \
  -H "Content-Type: application/json" \
  -d '{"timestamp": 12345, "relativePitch": -10.5}'

# 성능 측정
time curl http://localhost:8000/health
```

## 문서 관리

### 📚 문서 업데이트 주기

- **운영 가이드**: 매월 검토 및 업데이트
- **API 문서**: 코드 변경 시 즉시 업데이트
- **아키텍처 문서**: 분기별 검토
- **장애 대응 매뉴얼**: 장애 발생 후 업데이트

### 📝 지식 관리

- 모든 장애는 포스트모템 작성
- 해결 방법은 위키에 문서화
- 자주 묻는 질문 FAQ 관리
- 온보딩 가이드 지속 개선
