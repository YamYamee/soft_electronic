-- 자세 분류 데이터베이스 초기화 스크립트

-- 자세 예측 로그 테이블
CREATE TABLE prediction_logs (
    id SERIAL PRIMARY KEY,
    timestamp_input BIGINT NOT NULL,
    relative_pitch FLOAT NOT NULL,
    predicted_posture INTEGER NOT NULL,
    confidence FLOAT NOT NULL,
    all_probabilities JSONB,
    client_ip INET,
    user_agent TEXT,
    created_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        model_version VARCHAR(50) DEFAULT '1.0.0'
);

-- 클라이언트 연결 로그 테이블
CREATE TABLE connection_logs (
    id SERIAL PRIMARY KEY,
    client_ip INET NOT NULL,
    user_agent TEXT,
    connected_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        disconnected_at TIMESTAMP
    WITH
        TIME ZONE,
        session_duration INTERVAL,
        total_predictions INTEGER DEFAULT 0
);

-- 모델 성능 메트릭 테이블
CREATE TABLE model_metrics (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50) NOT NULL,
    accuracy FLOAT,
    precision_scores JSONB,
    recall_scores JSONB,
    f1_scores JSONB,
    feature_importance JSONB,
    training_samples INTEGER,
    created_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 시스템 상태 로그 테이블
CREATE TABLE system_status (
    id SERIAL PRIMARY KEY,
    server_status VARCHAR(20) NOT NULL, -- 'healthy', 'warning', 'error'
    active_connections INTEGER DEFAULT 0,
    cpu_usage FLOAT,
    memory_usage FLOAT,
    disk_usage FLOAT,
    response_time_ms FLOAT,
    error_count INTEGER DEFAULT 0,
    timestamp TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 자세 데이터 훈련 이력 테이블
CREATE TABLE training_data (
    id SERIAL PRIMARY KEY,
    person_name VARCHAR(50) NOT NULL,
    posture_number INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    sample_count INTEGER,
    mean_pitch FLOAT,
    std_pitch FLOAT,
    min_pitch FLOAT,
    max_pitch FLOAT,
    created_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        last_used_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_prediction_logs_created_at ON prediction_logs (created_at);

CREATE INDEX idx_prediction_logs_posture ON prediction_logs (predicted_posture);

CREATE INDEX idx_prediction_logs_client_ip ON prediction_logs (client_ip);

CREATE INDEX idx_connection_logs_connected_at ON connection_logs (connected_at);

CREATE INDEX idx_connection_logs_client_ip ON connection_logs (client_ip);

CREATE INDEX idx_model_metrics_version ON model_metrics (model_version);

CREATE INDEX idx_model_metrics_created_at ON model_metrics (created_at);

CREATE INDEX idx_system_status_timestamp ON system_status (timestamp);

CREATE INDEX idx_system_status_server_status ON system_status (server_status);

CREATE INDEX idx_training_data_person_posture ON training_data (person_name, posture_number);

-- 뷰 생성: 실시간 대시보드용
CREATE VIEW dashboard_stats AS
SELECT
    COUNT(*) as total_predictions,
    COUNT(DISTINCT client_ip) as unique_clients,
    AVG(confidence) as avg_confidence,
    mode () WITHIN GROUP (
        ORDER BY predicted_posture
    ) as most_common_posture,
    DATE_TRUNC ('hour', created_at) as hour_bucket
FROM prediction_logs
WHERE
    created_at >= NOW() - INTERVAL '24 hours'
GROUP BY
    hour_bucket
ORDER BY hour_bucket DESC;

-- 뷰 생성: 자세별 통계
CREATE VIEW posture_statistics AS
SELECT
    predicted_posture,
    COUNT(*) as prediction_count,
    AVG(confidence) as avg_confidence,
    MIN(confidence) as min_confidence,
    MAX(confidence) as max_confidence,
    STDDEV(confidence) as std_confidence,
    COUNT(DISTINCT client_ip) as unique_users
FROM prediction_logs
GROUP BY
    predicted_posture
ORDER BY predicted_posture;

-- 함수: 예측 로그 삽입
CREATE OR REPLACE FUNCTION insert_prediction_log(
    p_timestamp_input BIGINT,
    p_relative_pitch FLOAT,
    p_predicted_posture INTEGER,
    p_confidence FLOAT,
    p_all_probabilities JSONB,
    p_client_ip INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_model_version VARCHAR(50) DEFAULT '1.0.0'
) RETURNS INTEGER AS $$
DECLARE
    new_id INTEGER;
BEGIN
    INSERT INTO prediction_logs (
        timestamp_input, relative_pitch, predicted_posture, 
        confidence, all_probabilities, client_ip, user_agent, model_version
    ) VALUES (
        p_timestamp_input, p_relative_pitch, p_predicted_posture,
        p_confidence, p_all_probabilities, p_client_ip, p_user_agent, p_model_version
    ) RETURNING id INTO new_id;
    
    RETURN new_id;
END;
$$ LANGUAGE plpgsql;

-- 함수: 연결 로그 업데이트
CREATE OR REPLACE FUNCTION update_connection_log(
    p_client_ip INET,
    p_user_agent TEXT DEFAULT NULL,
    p_disconnect BOOLEAN DEFAULT FALSE
) RETURNS VOID AS $$
BEGIN
    IF p_disconnect THEN
        UPDATE connection_logs 
        SET disconnected_at = CURRENT_TIMESTAMP,
            session_duration = CURRENT_TIMESTAMP - connected_at
        WHERE client_ip = p_client_ip 
        AND disconnected_at IS NULL;
    ELSE
        INSERT INTO connection_logs (client_ip, user_agent)
        VALUES (p_client_ip, p_user_agent)
        ON CONFLICT DO NOTHING;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 더미 데이터 삽입 (테스트용)
INSERT INTO
    model_metrics (
        model_version,
        accuracy,
        training_samples
    )
VALUES ('1.0.0', 0.85, 23);

INSERT INTO
    system_status (
        server_status,
        active_connections,
        response_time_ms
    )
VALUES ('healthy', 0, 50.0);

-- 권한 설정
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO posture_user;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO posture_user;

GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO posture_user;