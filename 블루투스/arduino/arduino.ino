#include "Wire.h"
#include "I2Cdev.h"
#include "MPU6050.h"
#include <SoftwareSerial.h>
#include <ArduinoJson.h>

// 블루투스 모듈 연결핀 (RX: 2, TX: 3)
SoftwareSerial mySerial(2, 3);
MPU6050 mpu;

int16_t ax, ay, az;
float baselinePitch = 0; // 기준 자세(pitch)를 저장할 변수

// 측정 상태를 제어하는 변수
bool isMeasuring = false;
unsigned long lastPrintTime = 0;
unsigned long measurementStartTime = 0;

// MPU6050 가속도 센서의 스케일 팩터
const float ACCEL_SCALE = 16384.0;

// 5초 동안 기준 자세(Baseline)를 측정하고 설정하는 함수
void setBaselineFor5Seconds() {
  float pitchSum = 0;
  int measurementCount = 0;
  
  // 5초의 시작 시간 기록
  unsigned long calibrationStartTime = millis();

  // 5초 동안 반복
  while (millis() - calibrationStartTime < 5000) {
    mpu.getAcceleration(&ax, &ay, &az);
    float ax_g = (float)ax / ACCEL_SCALE;
    float ay_g = (float)ay / ACCEL_SCALE;
    float az_g = (float)az / ACCEL_SCALE;
    float denom = sqrt(ay_g * ay_g + az_g * az_g);

    if (denom < 1e-3) continue; // 0으로 나누는 것 방지

    float pitch = atan2(ax_g, denom) * 180.0 / PI;
    pitchSum += pitch;
    measurementCount++;
    delay(20); // 20ms 간격으로 측정
  }

  // 5초 동안 측정한 값의 평균을 기준 자세로 설정
  if (measurementCount > 0) {
    baselinePitch = pitchSum / measurementCount;
    Serial.print("새로운 기준 pitch 저장 완료: ");
    Serial.println(baselinePitch);
  }
}


void setup() {
  Serial.begin(9600);
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
          
          // --- Start 명령 수신 시, 5초간 기준 자세 설정 ---
          mySerial.println("{\"status\":\"Calibration starting... Hold your posture for 5 seconds.\"}");
          Serial.println("기준 자세 측정을 시작합니다. 5초간 자세를 유지해주세요...");
          
          setBaselineFor5Seconds(); // 5초간 기준 자세 설정 함수 호출
          
          mySerial.println("{\"status\":\"Calibration complete. Measurement started.\"}");
          Serial.println("기준 자세 설정 완료. 측정을 시작합니다.");
          
          // 측정 시작 상태로 전환
          isMeasuring = true;
          measurementStartTime = millis();
          lastPrintTime = measurementStartTime;

        }
        // "stop" 명령을 받고, 현재 측정 중일 때
        else if (strcmp(command, "stop") == 0 && isMeasuring) {
          isMeasuring = false;
          mySerial.println("{\"status\":\"Measurement stopped\"}");
          Serial.println("측정이 중지되었습니다. 다시 시작하려면 start 명령을 보내세요.");
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