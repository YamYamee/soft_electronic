import serial
import csv
import time

# 아두이노 시리얼 포트 설정
PORT = 'COM5'          # 사용 중인 포트로 변경하세요
BAUD = 115200
CSV_FILE = '7번자세.csv'

# 시리얼 포트 열기
ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)  # 아두이노 초기화 대기

print("⏳ 1초 후 측정 시작...")
time.sleep(1)

print("📡 시리얼 수신 시작... (1초 간격, Ctrl+C로 종료 가능)")

with open(CSV_FILE, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['timestamp_ms', 'relative_pitch_deg'])  # CSV 헤더 작성

    start_time = time.time()
    last_written_sec = -1
    pitch_offset = None  # 초기값 저장용

    try:
        while True:
            line = ser.readline().decode('utf-8').strip()

            if line and ',' in line:
                parts = line.split(',')
                if len(parts) == 2:
                    try:
                        _ = int(parts[0])  # 아두이노 타임스탬프는 무시
                        pitch = float(parts[1])

                        if pitch_offset is None:
                            pitch_offset = pitch  # 최초 pitch 저장

                        current_time = time.time()
                        current_sec = int(current_time - start_time)

                        if current_sec > last_written_sec:
                            relative_pitch = pitch - pitch_offset
                            timestamp_ms = int((current_time - start_time) * 1000)

                            writer.writerow([timestamp_ms, relative_pitch])
                            print(f"✅ 기록됨: {timestamp_ms}ms, 보정된 pitch: {relative_pitch:.2f}")
                            last_written_sec = current_sec

                    except ValueError:
                        continue  # 변환 실패 시 무시

    except KeyboardInterrupt:
        print("\n🛑 종료됨.")
    finally:
        ser.close()
