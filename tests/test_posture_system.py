"""
자세 분류 시스템 유닛 테스트
"""
import pytest
import pandas as pd
import numpy as np
import json
from unittest.mock import Mock, patch
from posture_classifier import PostureClassifier
from websocket_server import app
from fastapi.testclient import TestClient

class TestPostureClassifier:
    """자세 분류기 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.classifier = PostureClassifier("test_data")
        
    def test_extract_features(self):
        """특징 추출 테스트"""
        # 테스트 데이터 생성
        test_data = pd.DataFrame({
            'timestamp_ms': [1000, 2000, 3000, 4000, 5000],
            'relative_pitch_deg': [-5.0, -3.0, -2.0, -4.0, -6.0]
        })
        
        # 특징 추출
        features = self.classifier.extract_features(test_data)
        
        # 검증
        assert 'mean_pitch' in features
        assert 'std_pitch' in features
        assert 'min_pitch' in features
        assert 'max_pitch' in features
        assert features['mean_pitch'] == -4.0
        assert features['min_pitch'] == -6.0
        assert features['max_pitch'] == -2.0
        
    def test_extract_features_empty_dataframe(self):
        """빈 데이터프레임 테스트"""
        empty_df = pd.DataFrame()
        features = self.classifier.extract_features(empty_df)
        assert features == {}
        
    def test_extract_features_single_point(self):
        """단일 포인트 테스트"""
        single_point = pd.DataFrame({
            'timestamp_ms': [1000],
            'relative_pitch_deg': [-5.0]
        })
        
        features = self.classifier.extract_features(single_point)
        
        assert features['mean_pitch'] == -5.0
        assert features['std_pitch'] == 0.0
        assert features['mean_diff'] == 0
        assert features['stability_ratio'] == 1.0

class TestWebSocketServer:
    """웹소켓 서버 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.client = TestClient(app)
        
    def test_health_endpoint(self):
        """헬스체크 엔드포인트 테스트"""
        response = self.client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "active_connections" in data
        assert "model_loaded" in data
        
    def test_home_page(self):
        """홈페이지 테스트"""
        response = self.client.get("/")
        assert response.status_code == 200
        assert "자세 분류 웹소켓 테스트" in response.text

@pytest.mark.asyncio
class TestWebSocketConnection:
    """웹소켓 연결 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.client = TestClient(app)
        
    def test_websocket_connection(self):
        """웹소켓 연결 테스트"""
        with self.client.websocket_connect("/ws") as websocket:
            # 연결 확인
            data = websocket.receive_json()
            assert data["type"] == "welcome"
            assert "자세 분류 웹소켓 서버에 연결되었습니다" in data["message"]
            
    @patch('posture_classifier.PostureClassifier.predict_posture')
    def test_websocket_prediction(self, mock_predict):
        """웹소켓 예측 테스트"""
        # Mock 설정
        mock_predict.return_value = {
            "predicted_posture": 2,
            "confidence": 0.85,
            "all_probabilities": {0: 0.05, 1: 0.10, 2: 0.85},
            "timestamp": 15420,
            "relative_pitch": -25.73
        }
        
        with self.client.websocket_connect("/ws") as websocket:
            # 환영 메시지 수신
            welcome = websocket.receive_json()
            assert welcome["type"] == "welcome"
            
            # 예측 요청 전송
            test_data = {
                "timestamp": 15420,
                "relativePitch": -25.73
            }
            websocket.send_json(test_data)
            
            # 예측 결과 수신
            response = websocket.receive_json()
            assert response["type"] == "prediction"
            assert response["predicted_posture"] == 2
            assert response["confidence"] == 0.85
            
    def test_websocket_invalid_data(self):
        """잘못된 데이터 테스트"""
        with self.client.websocket_connect("/ws") as websocket:
            # 환영 메시지 수신
            welcome = websocket.receive_json()
            
            # 잘못된 JSON 전송
            websocket.send_text("invalid json")
            
            # 오류 응답 확인
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "잘못된 JSON 형식" in response["error"]
            
    def test_websocket_missing_fields(self):
        """필수 필드 누락 테스트"""
        with self.client.websocket_connect("/ws") as websocket:
            # 환영 메시지 수신
            welcome = websocket.receive_json()
            
            # 필수 필드 누락된 데이터 전송
            invalid_data = {"timestamp": 15420}  # relativePitch 누락
            websocket.send_json(invalid_data)
            
            # 오류 응답 확인
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "필수 필드가 누락되었습니다" in response["error"]

class TestDatabaseIntegration:
    """데이터베이스 통합 테스트"""
    
    @pytest.mark.skipif(not pytest.db_available, reason="Database not available")
    def test_prediction_log_insertion(self):
        """예측 로그 삽입 테스트"""
        # 실제 데이터베이스 테스트 코드
        pass
        
    @pytest.mark.skipif(not pytest.db_available, reason="Database not available")
    def test_connection_log_tracking(self):
        """연결 로그 추적 테스트"""
        # 실제 데이터베이스 테스트 코드
        pass

class TestModelPerformance:
    """모델 성능 테스트"""
    
    def test_model_prediction_speed(self):
        """모델 예측 속도 테스트"""
        classifier = PostureClassifier()
        
        # 더미 모델 설정
        classifier.model = Mock()
        classifier.scaler = Mock()
        classifier.feature_columns = ['mean_pitch', 'std_pitch']
        
        classifier.model.predict.return_value = [1]
        classifier.model.predict_proba.return_value = [[0.1, 0.9]]
        classifier.model.classes_ = [0, 1]
        classifier.scaler.transform.return_value = [[0.5, 0.3]]
        
        import time
        start_time = time.time()
        
        # 100번 예측 실행
        for _ in range(100):
            result = classifier.predict_posture(15420, -25.73)
            
        end_time = time.time()
        avg_time = (end_time - start_time) / 100
        
        # 평균 예측 시간이 100ms 이하여야 함
        assert avg_time < 0.1, f"예측 시간이 너무 느림: {avg_time:.3f}초"
        
    def test_model_memory_usage(self):
        """모델 메모리 사용량 테스트"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 모델 로드
        classifier = PostureClassifier()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 메모리 증가량이 100MB 이하여야 함
        assert memory_increase < 100 * 1024 * 1024, f"메모리 사용량이 너무 큼: {memory_increase / 1024 / 1024:.1f}MB"

def pytest_configure(config):
    """pytest 설정"""
    # 데이터베이스 가용성 확인
    try:
        import psycopg2
        pytest.db_available = True
    except ImportError:
        pytest.db_available = False
