"""
FastAPI 웹소켓 서버 - 자세 분류 API
"""

import asyncio
import json
import logging
import os
import traceback
from datetime import datetime
from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from posture_classifier import PostureClassifier

# .env 파일 로드 (있다면)
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv가 설치되지 않은 경우 무시
    pass

# 환경 변수 로드
SERVER_HOST = os.getenv("SERVER_HOST", "localhost")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("websocket_server.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

app = FastAPI(title="자세 분류 웹소켓 서버", version="1.0.0")


class ConnectionManager:
    """웹소켓 연결 관리자"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """새로운 웹소켓 연결 수락"""
        await websocket.accept()
        self.active_connections.append(websocket)
        client_host = websocket.client.host if websocket.client else "unknown"
        logger.info(
            f"새로운 클라이언트 연결: {client_host} (총 {len(self.active_connections)}개 연결)"
        )

    def disconnect(self, websocket: WebSocket):
        """웹소켓 연결 해제"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        client_host = websocket.client.host if websocket.client else "unknown"
        logger.info(
            f"클라이언트 연결 해제: {client_host} (남은 연결: {len(self.active_connections)}개)"
        )

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """특정 클라이언트에게 메시지 전송"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"메시지 전송 실패: {e}")

    async def broadcast(self, message: dict):
        """모든 연결된 클라이언트에게 메시지 브로드캐스트"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"브로드캐스트 실패: {e}")
                disconnected.append(connection)

        # 연결이 끊어진 클라이언트 제거
        for connection in disconnected:
            self.disconnect(connection)


# 전역 객체들
manager = ConnectionManager()
classifier = PostureClassifier()


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    logger.info("자세 분류 웹소켓 서버 시작")

    # 기존 모델 로드 시도
    if not classifier.load_model():
        logger.info("기존 모델이 없습니다. 새로운 모델을 학습합니다.")
        try:
            classifier.train_model()
            classifier.save_model()
            logger.info("모델 학습 및 저장 완료")
        except Exception as e:
            logger.error(f"모델 학습 실패: {e}")
            logger.error(traceback.format_exc())
    else:
        logger.info("기존 모델 로드 완료")


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 정리"""
    logger.info("자세 분류 웹소켓 서버 종료")


@app.get("/")
async def get():
    """홈페이지 - 웹소켓 테스트 클라이언트"""
    return HTMLResponse(
        content="""
<!DOCTYPE html>
<html>
<head>
    <title>자세 분류 웹소켓 테스트</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .input-group { margin: 10px 0; }
        label { display: inline-block; width: 150px; font-weight: bold; }
        input[type="number"] { width: 200px; padding: 5px; }
        button { 
            background-color: #4CAF50; 
            color: white; 
            padding: 10px 20px; 
            border: none; 
            cursor: pointer; 
            margin: 5px;
        }
        button:hover { background-color: #45a049; }
        button:disabled { background-color: #cccccc; cursor: not-allowed; }
        .output { 
            background-color: #f5f5f5; 
            padding: 15px; 
            margin: 20px 0; 
            border-radius: 5px; 
            min-height: 300px;
            max-height: 400px;
            overflow-y: auto;
        }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .connected { background-color: #d4edda; color: #155724; }
        .disconnected { background-color: #f8d7da; color: #721c24; }
        .prediction { 
            background-color: #d1ecf1; 
            color: #0c5460; 
            padding: 10px; 
            margin: 5px 0; 
            border-radius: 3px; 
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>자세 분류 웹소켓 테스트</h1>
        
        <div id="status" class="status disconnected">연결되지 않음</div>
        
        <button id="connectBtn" onclick="connect()">연결</button>
        <button id="disconnectBtn" onclick="disconnect()" disabled>연결 해제</button>
        
        <div class="input-group">
            <label for="timestamp">Timestamp (ms):</label>
            <input type="number" id="timestamp" value="15420">
        </div>
        
        <div class="input-group">
            <label for="relativePitch">Relative Pitch:</label>
            <input type="number" id="relativePitch" step="0.01" value="-25.73">
        </div>
        
        <button id="sendBtn" onclick="sendData()" disabled>데이터 전송</button>
        <button onclick="sendRandomData()" id="randomBtn" disabled>랜덤 데이터 전송</button>
        <button onclick="clearOutput()">출력 지우기</button>
        
        <div class="output" id="output"></div>
    </div>

    <script>
        let ws = null;
        const output = document.getElementById('output');
        const status = document.getElementById('status');
        const connectBtn = document.getElementById('connectBtn');
        const disconnectBtn = document.getElementById('disconnectBtn');
        const sendBtn = document.getElementById('sendBtn');
        const randomBtn = document.getElementById('randomBtn');

        function addToOutput(message, className = '') {
            const div = document.createElement('div');
            div.className = className;
            div.innerHTML = `<strong>[${new Date().toLocaleTimeString()}]</strong> ${message}`;
            output.appendChild(div);
            output.scrollTop = output.scrollHeight;
        }

        function updateStatus(connected) {
            if (connected) {
                status.textContent = '연결됨';
                status.className = 'status connected';
                connectBtn.disabled = true;
                disconnectBtn.disabled = false;
                sendBtn.disabled = false;
                randomBtn.disabled = false;
            } else {
                status.textContent = '연결되지 않음';
                status.className = 'status disconnected';
                connectBtn.disabled = false;
                disconnectBtn.disabled = true;
                sendBtn.disabled = true;
                randomBtn.disabled = true;
            }
        }

        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                addToOutput('웹소켓 연결 성공');
                updateStatus(true);
            };
            
            ws.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    let message = '';
                    
                    if (data.error) {
                        message = `❌ 오류: ${data.error}`;
                    } else if (data.predicted_posture !== undefined) {
                        message = `✅ 예측 결과: <strong>${data.predicted_posture}번 자세</strong> (확신도: ${(data.confidence * 100).toFixed(1)}%)`;
                    } else {
                        message = `📩 메시지: ${JSON.stringify(data, null, 2)}`;
                    }
                    
                    addToOutput(message, 'prediction');
                } catch (e) {
                    addToOutput(`📩 메시지: ${event.data}`);
                }
            };
            
            ws.onerror = function(error) {
                addToOutput(`❌ 웹소켓 오류: ${error}`);
            };
            
            ws.onclose = function() {
                addToOutput('웹소켓 연결 종료');
                updateStatus(false);
                ws = null;
            };
        }

        function disconnect() {
            if (ws) {
                ws.close();
            }
        }

        function sendData() {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                addToOutput('❌ 웹소켓이 연결되지 않았습니다.');
                return;
            }
            
            const timestamp = parseInt(document.getElementById('timestamp').value);
            const relativePitch = parseFloat(document.getElementById('relativePitch').value);
            
            const data = {
                timestamp: timestamp,
                relativePitch: relativePitch
            };
            
            ws.send(JSON.stringify(data));
            addToOutput(`📤 전송: timestamp=${timestamp}, relativePitch=${relativePitch}`);
        }

        function sendRandomData() {
            // 랜덤 데이터 생성
            const timestamp = Date.now();
            const relativePitch = (Math.random() - 0.5) * 60; // -30 ~ 30 범위
            
            document.getElementById('timestamp').value = timestamp;
            document.getElementById('relativePitch').value = relativePitch.toFixed(2);
            
            sendData();
        }

        function clearOutput() {
            output.innerHTML = '';
        }

        // 엔터 키로 데이터 전송
        document.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !sendBtn.disabled) {
                sendData();
            }
        });
    </script>
</body>
</html>
    """
    )


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(manager.active_connections),
        "model_loaded": classifier.model is not None,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """웹소켓 엔드포인트"""
    await manager.connect(websocket)

    try:
        # 연결 환영 메시지
        welcome_message = {
            "type": "welcome",
            "message": "자세 분류 웹소켓 서버에 연결되었습니다.",
            "timestamp": datetime.now().isoformat(),
            "instructions": '다음 형식으로 데이터를 전송해주세요: {"timestamp": 15420, "relativePitch": -25.73}',
        }
        await manager.send_personal_message(welcome_message, websocket)

        while True:
            # 클라이언트로부터 데이터 수신
            data = await websocket.receive_text()

            try:
                # JSON 파싱
                request_data = json.loads(data)
                logger.info(f"수신된 데이터: {request_data}")

                # 데이터 검증
                if (
                    "timestamp" not in request_data
                    or "relativePitch" not in request_data
                ):
                    error_response = {
                        "type": "error",
                        "error": "필수 필드가 누락되었습니다. timestamp와 relativePitch가 필요합니다.",
                        "timestamp": datetime.now().isoformat(),
                    }
                    await manager.send_personal_message(error_response, websocket)
                    continue

                timestamp = request_data["timestamp"]
                relative_pitch = request_data["relativePitch"]

                # 데이터 타입 검증
                if not isinstance(timestamp, (int, float)) or not isinstance(
                    relative_pitch, (int, float)
                ):
                    error_response = {
                        "type": "error",
                        "error": "timestamp와 relativePitch는 숫자여야 합니다.",
                        "timestamp": datetime.now().isoformat(),
                    }
                    await manager.send_personal_message(error_response, websocket)
                    continue

                # 자세 예측
                if classifier.model is None:
                    error_response = {
                        "type": "error",
                        "error": "모델이 로드되지 않았습니다. 서버를 다시 시작해주세요.",
                        "timestamp": datetime.now().isoformat(),
                    }
                    await manager.send_personal_message(error_response, websocket)
                    continue

                # 예측 수행
                prediction_result = classifier.predict_posture(
                    int(timestamp), float(relative_pitch)
                )

                if "error" in prediction_result:
                    error_response = {
                        "type": "error",
                        "error": prediction_result["error"],
                        "timestamp": datetime.now().isoformat(),
                    }
                    await manager.send_personal_message(error_response, websocket)
                else:
                    # 성공적인 예측 결과 전송
                    response = {
                        "type": "prediction",
                        "predicted_posture": prediction_result["predicted_posture"],
                        "confidence": prediction_result["confidence"],
                        "all_probabilities": prediction_result["all_probabilities"],
                        "input_timestamp": prediction_result["timestamp"],
                        "input_relative_pitch": prediction_result["relative_pitch"],
                        "server_timestamp": datetime.now().isoformat(),
                    }
                    await manager.send_personal_message(response, websocket)

                    logger.info(
                        f"예측 완료 - 입력: {relative_pitch}도, 결과: {prediction_result['predicted_posture']}번 자세"
                    )

            except json.JSONDecodeError:
                error_response = {
                    "type": "error",
                    "error": "잘못된 JSON 형식입니다.",
                    "timestamp": datetime.now().isoformat(),
                }
                await manager.send_personal_message(error_response, websocket)
                logger.warning(f"잘못된 JSON 데이터 수신: {data}")

            except Exception as e:
                error_response = {
                    "type": "error",
                    "error": f"처리 중 오류 발생: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                }
                await manager.send_personal_message(error_response, websocket)
                logger.error(f"데이터 처리 중 오류: {e}")
                logger.error(traceback.format_exc())

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("클라이언트가 연결을 끊었습니다.")
    except Exception as e:
        logger.error(f"웹소켓 처리 중 예상치 못한 오류: {e}")
        logger.error(traceback.format_exc())
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    logger.info(f"서버 시작: {SERVER_HOST}:{SERVER_PORT} (환경: {ENVIRONMENT})")
    uvicorn.run(
        app,
        host="0.0.0.0",  # 모든 인터페이스에서 접근 가능
        port=SERVER_PORT,
        log_level=LOG_LEVEL.lower(),
    )
