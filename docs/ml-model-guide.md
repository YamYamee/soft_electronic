# 🧠 ML 모델 가이드

## 개요

자세 분류 시스템의 핵심인 머신러닝 모델에 대한 상세 가이드입니다.

## 모델 아키텍처

### 1. 데이터 전처리

```python
# 입력 데이터 형태
{
    "timestamp": 15420,      # 밀리초 단위 타임스탬프
    "relativePitch": -25.73  # 상대 피치 각도 (도)
}
```

### 2. 특징 추출 (Feature Engineering)

총 14개의 통계적 특징을 추출합니다:

#### 기본 통계량

- `mean_pitch`: 평균 피치 값
- `std_pitch`: 피치의 표준편차
- `min_pitch`: 최소 피치 값
- `max_pitch`: 최대 피치 값
- `median_pitch`: 피치의 중앙값
- `q25_pitch`: 25% 분위수
- `q75_pitch`: 75% 분위수
- `range_pitch`: 피치 범위 (max - min)

#### 분포 특성

- `skewness_pitch`: 피치 분포의 비대칭도
- `kurtosis_pitch`: 피치 분포의 첨도

#### 변화율 특성

- `mean_diff`: 평균 변화율
- `std_diff`: 변화율의 표준편차
- `max_diff`: 최대 변화율

#### 안정성 특성

- `stability_ratio`: 안정한 구간의 비율 (변화량 < 1도)

### 3. 모델 알고리즘

**Random Forest Classifier**를 사용하는 이유:

- 과적합 방지
- 특징 중요도 제공
- 빠른 예측 속도
- 노이즈에 강함

```python
RandomForestClassifier(
    n_estimators=100,      # 트리 개수
    random_state=42,       # 재현성 보장
    max_depth=10,         # 최대 깊이
    min_samples_split=5,  # 분할 최소 샘플
    min_samples_leaf=2    # 리프 최소 샘플
)
```

## 학습 데이터

### 데이터 소스

- **다혜**: 8개 자세 파일
- **도엽**: 7개 자세 파일 (5번 제외)
- **준형**: 8개 자세 파일

### 자세 분류

| 번호 | 자세 설명   | 특징           |
| ---- | ----------- | -------------- |
| 0    | 기본 자세   | 중립적 피치 값 |
| 1    | 전방 기울임 | 음수 피치 값   |
| 2    | 후방 기울임 | 양수 피치 값   |
| 3    | 좌측 기울임 | 좌측 편향      |
| 4    | 우측 기울임 | 우측 편향      |
| 5    | 복합 자세 1 | 혼합 패턴      |
| 6    | 복합 자세 2 | 불규칙 패턴    |
| 7    | 복합 자세 3 | 동적 패턴      |

### 데이터 분포

```python
자세 분포: {
    0: 3개 샘플,  # 기본 자세
    1: 3개 샘플,  # 전방 기울임
    2: 3개 샘플,  # 후방 기울임
    3: 3개 샘플,  # 좌측 기울임
    4: 3개 샘플,  # 우측 기울임
    5: 2개 샘플,  # 복합 자세 1
    6: 3개 샘플,  # 복합 자세 2
    7: 3개 샘플   # 복합 자세 3
}
```

## 모델 성능

### 평가 지표

- **정확도 (Accuracy)**: 전체 예측 중 맞춘 비율
- **정밀도 (Precision)**: 예측한 자세 중 실제 맞춘 비율
- **재현율 (Recall)**: 실제 자세 중 예측한 비율
- **F1-Score**: 정밀도와 재현율의 조화평균
- **혼동 행렬 (Confusion Matrix)**: 자세별 예측 성능

### 특징 중요도

모델이 자동으로 계산한 특징별 중요도:

```python
특징 중요도:
1. mean_diff (14.4%)      # 평균 변화율
2. mean_pitch (9.0%)      # 평균 피치
3. kurtosis_pitch (8.1%)  # 분포 첨도
4. q75_pitch (7.6%)       # 75% 분위수
5. max_pitch (7.5%)       # 최대 피치
```

## 모델 사용법

### 1. 모델 학습

```bash
# 새로운 데이터로 모델 재훈련
python posture_classifier.py
```

### 2. 모델 로드 및 예측

```python
from posture_classifier import PostureClassifier

# 분류기 초기화
classifier = PostureClassifier()

# 기존 모델 로드
classifier.load_model("posture_model.pkl")

# 예측 수행
result = classifier.predict_posture(
    timestamp=15420,
    relative_pitch=-25.73
)

print(f"예측 자세: {result['predicted_posture']}")
print(f"확신도: {result['confidence']:.2%}")
```

### 3. 예측 결과 해석

```python
{
    "predicted_posture": 2,        # 예측된 자세 번호
    "confidence": 0.85,            # 확신도 (0-1)
    "all_probabilities": {         # 모든 자세별 확률
        "0": 0.05,
        "1": 0.10,
        "2": 0.85,  # 가장 높은 확률
        "3": 0.00
    },
    "timestamp": 15420,
    "relative_pitch": -25.73
}
```

## 모델 개선 방안

### 1. 데이터 증강

- 더 많은 사용자 데이터 수집
- 다양한 환경에서의 데이터 수집
- 시뮬레이션 데이터 생성

### 2. 특징 엔지니어링

- 주파수 도메인 특징 추가
- 시간 윈도우 특징 추가
- 센서 융합 특징 추가

### 3. 모델 알고리즘

- XGBoost, LightGBM 실험
- 딥러닝 모델 (LSTM, CNN) 실험
- 앙상블 방법 적용

### 4. 하이퍼파라미터 튜닝

```python
# GridSearchCV를 사용한 최적화
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}
```

## 모델 모니터링

### 1. 성능 지표 추적

- 실시간 정확도 모니터링
- 자세별 예측 분포 추적
- 확신도 분포 분석

### 2. 데이터 드리프트 감지

- 입력 데이터 분포 변화 감지
- 예측 성능 저하 감지
- 자동 재훈련 트리거

### 3. A/B 테스트

- 새로운 모델과 기존 모델 비교
- 점진적 배포를 통한 리스크 최소화
- 사용자 피드백 수집

## 모델 버전 관리

### 1. 모델 아티팩트

```
models/
├── v1.0.0/
│   ├── posture_model.pkl      # 모델 파일
│   ├── scaler.pkl             # 스케일러
│   ├── feature_columns.json   # 특징 컬럼
│   └── metadata.json          # 메타데이터
├── v1.1.0/
└── v1.2.0/
```

### 2. 메타데이터 관리

```json
{
  "version": "1.0.0",
  "created_at": "2025-08-27T00:00:00Z",
  "training_samples": 23,
  "accuracy": 0.85,
  "features": 14,
  "algorithm": "RandomForest",
  "hyperparameters": {
    "n_estimators": 100,
    "max_depth": 10
  }
}
```

### 3. 롤백 전략

- 이전 버전 모델 자동 백업
- 성능 저하 감지 시 자동 롤백
- 수동 롤백 API 제공

## 문제 해결

### 1. 낮은 정확도

- 데이터 품질 확인
- 특징 중요도 분석
- 하이퍼파라미터 조정

### 2. 느린 예측 속도

- 모델 경량화
- 특징 수 줄이기
- 캐싱 활용

### 3. 메모리 부족

- 모델 압축
- 배치 처리 최적화
- 가비지 컬렉션 조정
