#include "Wire.h"
#include "I2Cdev.h"
#include "MPU6050.h"

MPU6050 mpu;
int16_t ax, ay, az;
float baselinePitch = 0;
bool baselineSet = false;

unsigned long lastPrintTime = 0;

const int STABILITY_WINDOW = 50;
const float STABILITY_THRESHOLD = 5.0;  // 2도까지 허용
const float ACCEL_SCALE = 16384.0;  // MPU6050 ±2g scale

void setup() {
  Wire.begin();
  Serial.begin(115200);
  mpu.initialize();

  if (!mpu.testConnection()) {
    Serial.println("MPU6050 연결 실패");
    while (1);
  }

  Serial.println("MPU6050 연결 성공");
  Serial.println("센서가 고정될 때까지 기다리는 중...");

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
        baselinePitch = sumPitch / STABILITY_WINDOW;
        baselineSet = true;
        Serial.print("기준 pitch 저장 완료: ");
        Serial.println(baselinePitch);
        break;
      }
      stableCount = 0;
    }
  }
}

void loop() {
  if (!baselineSet) return;

  mpu.getAcceleration(&ax, &ay, &az);

  float ax_g = (float)ax / ACCEL_SCALE;
  float ay_g = (float)ay / ACCEL_SCALE;
  float az_g = (float)az / ACCEL_SCALE;

  float denom = sqrt(ay_g * ay_g + az_g * az_g);
  if (denom < 1e-3) return;

  float pitch = atan2(ax_g, denom) * 180.0 / PI;
  float relativePitch = pitch - baselinePitch;

  unsigned long now = millis();
  if (now - lastPrintTime >= 1000) {
    Serial.print(now);
    Serial.print(",");
    Serial.println(relativePitch, 2);
    lastPrintTime = now;
  }
}
