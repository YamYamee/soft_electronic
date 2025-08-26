"""
pytest 설정 및 fixture 정의
"""
import sys
from pathlib import Path

import pytest

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 데이터베이스 가용성 확인
try:
    import psycopg2
    db_available = True
except ImportError:
    db_available = False

def pytest_configure(config):
    """pytest 설정"""
    pytest.db_available = db_available
    
def pytest_collection_modifyitems(config, items):
    """테스트 수집 후 수정"""
    skip_db = pytest.mark.skip(reason="Database not available")
    for item in items:
        if "database" in item.keywords and not db_available:
            item.add_marker(skip_db)

@pytest.fixture(scope="session")
def test_data_dir():
    """테스트 데이터 디렉토리 경로"""
    return project_root / "자세모음"

@pytest.fixture(scope="session") 
def model_file():
    """모델 파일 경로"""
    return project_root / "posture_model.pkl"

@pytest.fixture
def sample_imu_data():
    """샘플 IMU 데이터"""
    return {
        "timestamp": 15420,
        "relativePitch": -25.73
    }

@pytest.fixture
def invalid_imu_data():
    """잘못된 IMU 데이터"""
    return {
        "timestamp": 15420
        # relativePitch 누락
    }
