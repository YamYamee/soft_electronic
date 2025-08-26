#include "Wire.h"
#include "I2Cdev.h"
#include "MPU6050.h"
#include <SoftwareSerial.h>
#include <ArduinoJson.h>

// 블루투스 모듈 연결핀 (RX: 2, TX: 3)
SoftwareSerial mySerial(2, 3);
MPU6050 mpu;

int16_t ax, ay, az;
float baselinePitch = 0;

// 측정 상태를 제어하는 변수
bool isMeasuring = false;
unsigned long lastPrintTime = 0;
unsigned long measurementStartTime = 0;

const float ACCEL_SCALE = 16384.0;
const int STABILITY_WINDOW = 50;
const float STABILITY_THRESHOLD = 5.0;

void setup() {
  Serial.begin(115200);
  mySerial.begin(9600);
  Wire.begin();
  mpu.initialize();

  if (!mpu.testConnection()) {
    Serial.println("MPU6050 연결 실패");
    while (1);
  }
  Serial.println("MPU6050 연결 성공. 앱의 시작(start) 명령을 기다립니다...");
  mySerial.println("{\"status\":\"Ready, waiting for start command\"}");
}

void loop() {
  // 1. 앱으로부터 명령 수신 처리
  if (mySerial.available() > 0) {
    String input = mySerial.readStringUntil('\n');
    StaticJsonDocument<128> doc;
    DeserializationError error = deserializeJson(doc, input);

    if (!error) {
      const char* command = doc["command"];
      if (command) {
        // "start" 명령을 받고, 현재 측정 중이 아닐 때
        if (strcmp(command, "start") == 0 && !isMeasuring) {
          // --- Start 명령 수신 시, 기준 자세 재설정 ---
          mySerial.println("{\"status\":\"Calibrating... Hold current posture.\"}");
          calibrateBaseline(); // 기준 자세 설정 함수 호출
          
          mySerial.println("{\"status\":\"Calibration complete. Starting measurement in 5 seconds...\"}");
          delay(5000); // 5초 대기
          
          isMeasuring = true;
          measurementStartTime = millis();
          lastPrintTime = measurementStartTime;
          mySerial.println("{\"status\":\"Measurement started\"}");
        }
        // "stop" 명령을 받고, 현재 측정 중일 때
        else if (strcmp(command, "stop") == 0 && isMeasuring) {
          isMeasuring = false;
          mySerial.println("{\"status\":\"Measurement stopped\"}");
        }
      }
    }
  }

  // 2. 측정 상태일 때만 1초마다 데이터 전송
  if (isMeasuring) {
    unsigned long now = millis();
    if (now - lastPrintTime >= 1000) {
      mpu.getAcceleration(&ax, &ay, &az);
      float ax_g = (float)ax / ACCEL_SCALE;
      float ay_g = (float)ay / ACCEL_SCALE;
      float az_g = (float)az / ACCEL_SCALE;
      float denom = sqrt(ay_g * ay_g + az_g * az_g);

      if (denom >= 1e-3) {
        float pitch = atan2(ax_g, denom) * 180.0 / PI;
        float relativePitch = pitch - baselinePitch;

        StaticJsonDocument<128> dataDoc;
        dataDoc["timestamp"] = now - measurementStartTime;
        dataDoc["relativePitch"] = relativePitch;

        serializeJson(dataDoc, mySerial);
        mySerial.println();
      }
      lastPrintTime = now;
    }
  }
}

// 기준 자세(Baseline)를 측정하고 설정하는 함수
void calibrateBaseline() {
  float pitchHistory[STABILITY_WINDOW] = {0};
  int stableCount = 0;
  
  while (true) {
    mpu.getAcceleration(&ax, &ay, &az);
    float ax_g = (float)ax / ACCEL_SCALE;
    float ay_g = (float)ay / ACCEL_SCALE;
    float az_g = (float)az / ACCEL_SCALE;
    float denom = sqrt(ay_g * ay_g + az_g * az_g);
    if (denom < 1e-3) continue;
    float pitch = atan2(ax_g, denom) * 180.0 / PI;

    pitchHistory[stableCount % STABILITY_WINDOW] = pitch;
    stableCount++;
    delay(20);

    if (stableCount >= STABILITY_WINDOW) {
      float minPitch = pitchHistory[0];
      float maxPitch = pitchHistory[0];
      float sumPitch = 0;
      for (int i = 0; i < STABILITY_WINDOW; i++) {
        if (pitchHistory[i] < minPitch) minPitch = pitchHistory[i];
        if (pitchHistory[i] > maxPitch) maxPitch = pitchHistory[i];
        sumPitch += pitchHistory[i];
      }
      if ((maxPitch - minPitch) < STABILITY_THRESHOLD) {
        baselinePitch = sumPitch / STABILITY_WINDOW; // 새로운 기준 자세 저장
        Serial.print("새로운 기준 pitch 저장 완료: ");
        Serial.println(baselinePitch);
        break; // 보정 완료 후 루프 탈출
      }
      stableCount = 0; // 안정화 실패 시 다시 시도
    }
  }
}