"""
자세 분류 시스템 패키지
"""

__version__ = "1.0.0"
__author__ = "Posture Classification Team"
__description__ = "실시간 IMU 센서 기반 자세 분류 시스템"

# 메인 모듈들을 import 가능하게 설정
try:
    from .posture_classifier import PostureClassifier
    from .websocket_server import app
except ImportError:
    # 상대 import가 실패하면 절대 import 시도
    pass
