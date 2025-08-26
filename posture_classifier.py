"""
자세 분류를 위한 머신러닝 모델
"""
import os
import glob
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from typing import Dict, List, Tuple, Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('posture_classifier.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PostureClassifier:
    def __init__(self, data_dir: str = "자세모음"):
        """
        자세 분류기 초기화
        
        Args:
            data_dir: 자세 데이터가 있는 디렉토리 경로
        """
        self.data_dir = data_dir
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.posture_labels = {}
        
    def extract_features(self, df: pd.DataFrame) -> Dict:
        """
        시계열 데이터에서 특징을 추출합니다.
        
        Args:
            df: timestamp_ms, relative_pitch_deg 컬럼이 있는 DataFrame
            
        Returns:
            추출된 특징들의 딕셔너리
        """
        if len(df) == 0:
            logger.warning("빈 데이터프레임에서 특징 추출 시도")
            return {}
            
        pitch_values = df['relative_pitch_deg'].values
        
        features = {
            'mean_pitch': np.mean(pitch_values),
            'std_pitch': np.std(pitch_values),
            'min_pitch': np.min(pitch_values),
            'max_pitch': np.max(pitch_values),
            'median_pitch': np.median(pitch_values),
            'q25_pitch': np.percentile(pitch_values, 25),
            'q75_pitch': np.percentile(pitch_values, 75),
            'range_pitch': np.max(pitch_values) - np.min(pitch_values),
            'skewness_pitch': pd.Series(pitch_values).skew(),
            'kurtosis_pitch': pd.Series(pitch_values).kurtosis(),
        }
        
        # 변화율 특징
        if len(pitch_values) > 1:
            diff_values = np.diff(pitch_values)
            features.update({
                'mean_diff': np.mean(diff_values),
                'std_diff': np.std(diff_values),
                'max_diff': np.max(np.abs(diff_values)),
            })
        else:
            features.update({
                'mean_diff': 0,
                'std_diff': 0,
                'max_diff': 0,
            })
            
        # 안정성 측정 (연속된 값들의 변화가 작은 구간의 비율)
        if len(pitch_values) > 1:
            stability_threshold = 1.0  # 1도 이하 변화를 안정적으로 간주
            stable_points = np.sum(np.abs(diff_values) < stability_threshold)
            features['stability_ratio'] = stable_points / len(diff_values)
        else:
            features['stability_ratio'] = 1.0
            
        return features
    
    def load_training_data(self) -> Tuple[pd.DataFrame, List[int]]:
        """
        자세모음 디렉토리에서 모든 자세 데이터를 로드합니다.
        
        Returns:
            features_df: 특징들이 포함된 DataFrame
            labels: 자세 번호 리스트
        """
        logger.info("학습 데이터 로딩 시작")
        
        all_features = []
        all_labels = []
        
        # 각 사람별 디렉토리 탐색 (다혜, 도엽, 준형만 사용)
        allowed_persons = ['다혜', '도엽', '준형']
        person_dirs = [d for d in os.listdir(self.data_dir) 
                      if os.path.isdir(os.path.join(self.data_dir, d)) and d in allowed_persons]
        
        logger.info(f"사용할 사람 디렉토리: {person_dirs}")
        
        for person in person_dirs:
            person_path = os.path.join(self.data_dir, person)
            csv_files = glob.glob(os.path.join(person_path, "*.csv"))
            
            logger.info(f"{person} - {len(csv_files)}개 파일 발견")
            
            for csv_file in csv_files:
                try:
                    # 파일명에서 자세 번호 추출
                    filename = os.path.basename(csv_file)
                    posture_num = int(filename.split('번자세')[0])
                    
                    # 데이터 로드
                    df = pd.read_csv(csv_file)
                    
                    # 컬럼명 확인 및 정규화
                    if 'relative_pitch_deg' not in df.columns:
                        # 다른 형식의 파일인 경우 건너뛰기
                        logger.warning(f"잘못된 형식의 파일 건너뜀: {csv_file}")
                        continue
                    
                    if len(df) == 0:
                        logger.warning(f"빈 파일: {csv_file}")
                        continue
                    
                    # 특징 추출
                    features = self.extract_features(df)
                    
                    if features:
                        all_features.append(features)
                        all_labels.append(posture_num)
                        
                        # 자세 라벨 기록
                        if posture_num not in self.posture_labels:
                            self.posture_labels[posture_num] = []
                        self.posture_labels[posture_num].append(f"{person}_{filename}")
                        
                except Exception as e:
                    logger.error(f"파일 {csv_file} 처리 중 오류: {e}")
                    continue
        
        if not all_features:
            logger.error("학습 데이터를 찾을 수 없습니다!")
            return pd.DataFrame(), []
        
        features_df = pd.DataFrame(all_features)
        
        # NaN 값 처리
        features_df = features_df.fillna(0)
        
        logger.info(f"총 {len(features_df)}개 샘플 로드 완료")
        logger.info(f"자세 분포: {dict(pd.Series(all_labels).value_counts().sort_index())}")
        
        return features_df, all_labels
    
    def train_model(self) -> None:
        """
        머신러닝 모델을 학습합니다.
        """
        logger.info("모델 학습 시작")
        
        # 데이터 로드
        features_df, labels = self.load_training_data()
        
        if len(features_df) == 0:
            logger.error("학습할 데이터가 없습니다!")
            return
        
        # 특징 컬럼 저장
        self.feature_columns = features_df.columns.tolist()
        
        # 데이터 정규화
        X_scaled = self.scaler.fit_transform(features_df)
        
        # 학습/테스트 분할 (데이터가 적을 경우 stratify 비활성화)
        unique_labels = np.unique(labels)
        min_class_count = min([labels.count(label) for label in unique_labels])
        
        if min_class_count < 2 or len(features_df) < 10:
            # 데이터가 너무 적으면 전체 데이터로 학습하고 자체 검증
            logger.warning("데이터가 부족하여 전체 데이터로 학습합니다.")
            X_train, X_test, y_train, y_test = X_scaled, X_scaled, labels, labels
        else:
            # 충분한 데이터가 있으면 정상적으로 분할
            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, labels, test_size=0.2, random_state=42, stratify=labels
                )
            except ValueError:
                # stratify가 실패하면 stratify 없이 분할
                logger.warning("Stratify 분할 실패, 일반 분할로 진행합니다.")
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, labels, test_size=0.2, random_state=42
                )
        
        # 모델 학습
        self.model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2
        )
        
        self.model.fit(X_train, y_train)
        
        # 모델 평가
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        logger.info(f"모델 정확도: {accuracy:.4f}")
        logger.info(f"분류 리포트:\n{classification_report(y_test, y_pred)}")
        
        # 특징 중요도
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info(f"특징 중요도:\n{feature_importance}")
        
    def predict_posture(self, timestamp: int, relative_pitch: float) -> Dict:
        """
        단일 데이터 포인트에서 자세를 예측합니다.
        
        Args:
            timestamp: 타임스탬프 (ms)
            relative_pitch: 상대 피치 각도
            
        Returns:
            예측 결과 딕셔너리
        """
        if self.model is None:
            logger.error("모델이 학습되지 않았습니다!")
            return {"error": "Model not trained"}
        
        try:
            # 단일 포인트로 DataFrame 생성
            df = pd.DataFrame({
                'timestamp_ms': [timestamp],
                'relative_pitch_deg': [relative_pitch]
            })
            
            # 특징 추출
            features = self.extract_features(df)
            
            if not features:
                logger.error("특징 추출 실패")
                return {"error": "Feature extraction failed"}
            
            # 특징 DataFrame 생성
            feature_df = pd.DataFrame([features])
            
            # 누락된 특징 처리
            for col in self.feature_columns:
                if col not in feature_df.columns:
                    feature_df[col] = 0
            
            # 컬럼 순서 맞추기
            feature_df = feature_df[self.feature_columns]
            
            # 정규화
            X_scaled = self.scaler.transform(feature_df)
            
            # 예측
            predicted_posture = self.model.predict(X_scaled)[0]
            prediction_proba = self.model.predict_proba(X_scaled)[0]
            
            # 확률 정보
            classes = self.model.classes_
            proba_dict = {int(cls): float(prob) for cls, prob in zip(classes, prediction_proba)}
            max_probability = max(prediction_proba)
            
            result = {
                "predicted_posture": int(predicted_posture),
                "confidence": float(max_probability),
                "all_probabilities": proba_dict,
                "timestamp": timestamp,
                "relative_pitch": relative_pitch
            }
            
            logger.info(f"예측 완료 - 자세: {predicted_posture}, 확신도: {max_probability:.4f}")
            
            return result
            
        except Exception as e:
            logger.error(f"예측 중 오류 발생: {e}")
            return {"error": str(e)}
    
    def save_model(self, model_path: str = "posture_model.pkl") -> None:
        """
        학습된 모델을 저장합니다.
        """
        if self.model is None:
            logger.error("저장할 모델이 없습니다!")
            return
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'posture_labels': self.posture_labels
        }
        
        joblib.dump(model_data, model_path)
        logger.info(f"모델이 {model_path}에 저장되었습니다.")
    
    def load_model(self, model_path: str = "posture_model.pkl") -> bool:
        """
        저장된 모델을 로드합니다.
        
        Returns:
            로드 성공 여부
        """
        try:
            if not os.path.exists(model_path):
                logger.warning(f"모델 파일이 존재하지 않습니다: {model_path}")
                return False
            
            model_data = joblib.load(model_path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            self.posture_labels = model_data['posture_labels']
            
            logger.info(f"모델이 {model_path}에서 로드되었습니다.")
            return True
            
        except Exception as e:
            logger.error(f"모델 로드 중 오류: {e}")
            return False

if __name__ == "__main__":
    # 모델 학습 및 저장
    classifier = PostureClassifier()
    classifier.train_model()
    classifier.save_model()
