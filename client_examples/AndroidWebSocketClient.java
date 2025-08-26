
// Android WebSocket 클라이언트 예시
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import org.json.JSONObject;
import java.net.URI;

public class PostureWebSocketClient {
    private WebSocketClient webSocketClient;
    private boolean isConnected = false;

    public void connect(String serverUrl) {
        try {
            URI serverUri = URI.create(serverUrl); // "ws://your-server:8000/ws"

            webSocketClient = new WebSocketClient(serverUri) {
                @Override
                public void onOpen(ServerHandshake handshake) {
                    isConnected = true;
                    System.out.println("자세 분류 서버에 연결됨");
                }

                @Override
                public void onMessage(String message) {
                    try {
                        JSONObject response = new JSONObject(message);
                        String type = response.getString("type");

                        if ("prediction".equals(type)) {
                            int predictedPosture = response.getInt("predicted_posture");
                            double confidence = response.getDouble("confidence");

                            System.out.println("예측 결과: " + predictedPosture + "번 자세");
                            System.out.println("확신도: " + (confidence * 100) + "%");

                            // UI 업데이트
                            onPosturePredicted(predictedPosture, confidence);

                        } else if ("error".equals(type)) {
                            String error = response.getString("error");
                            System.err.println("서버 오류: " + error);
                            onError(error);
                        }

                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                }

                @Override
                public void onClose(int code, String reason, boolean remote) {
                    isConnected = false;
                    System.out.println("연결 종료: " + reason);
                }

                @Override
                public void onError(Exception ex) {
                    System.err.println("WebSocket 오류: " + ex.getMessage());
                    onError(ex.getMessage());
                }
            };

            webSocketClient.connect();

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void sendPostureData(long timestamp, double relativePitch) {
        if (!isConnected || webSocketClient == null) {
            System.err.println("서버에 연결되지 않음");
            return;
        }

        try {
            JSONObject data = new JSONObject();
            data.put("timestamp", timestamp);
            data.put("relativePitch", relativePitch);

            webSocketClient.send(data.toString());
            System.out.println("데이터 전송: " + data.toString());

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void disconnect() {
        if (webSocketClient != null) {
            webSocketClient.close();
        }
    }

    // 콜백 메서드들 (앱에서 구현해야 함)
    private void onPosturePredicted(int posture, double confidence) {
        // UI 스레드에서 실행
        // 예: 자세 결과를 화면에 표시
    }

    private void onError(String error) {
        // 오류 처리
        // 예: 토스트 메시지 표시
    }
}

// 사용 예시
public class MainActivity extends AppCompatActivity {
    private PostureWebSocketClient client;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        client = new PostureWebSocketClient();
        
        // 설정에서 서버 주소 읽기 (권장)
        String serverUrl = getServerUrl();
        client.connect(serverUrl);
    }
    
    // 서버 URL 설정 (환경에 따라 변경)
    private String getServerUrl() {
        // SharedPreferences나 BuildConfig에서 읽어오기
        return getString(R.string.posture_server_url); // strings.xml에서 관리
        
        // 또는 환경별 설정
        // if (BuildConfig.DEBUG) {
        //     return "ws://10.0.2.2:8000/ws";  // 에뮬레이터용
        // } else {
        //     return "ws://your-production-server.com:8000/ws";
        // }
    }

    // IMU 센서에서 데이터를 받았을 때
    private void onIMUDataReceived(float pitch) {
        long timestamp = System.currentTimeMillis();
        client.sendPostureData(timestamp, pitch);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (client != null) {
            client.disconnect();
        }
    }
}
