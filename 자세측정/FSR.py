import serial
import time
import datetime
import sys

try:
    import msvcrt  # Windows 비차단 키보드 입력
    WINDOWS = True
except ImportError:
    WINDOWS = False  # (필요 시: Unix에서는 다른 방식 필요)

SERIAL_PORT = 'COM6'
BAUD_RATE = 9600
current_datetime = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_FILENAME = f'pressure_data_{current_datetime}.csv'

def setup_serial_connection():
    """시리얼 포트를 열고 아두이노와의 연결을 설정합니다."""
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # 아두이노 리셋 대기
        print(f"아두이노와 시리얼 연결됨: {SERIAL_PORT} @ {BAUD_RATE} bps")
        return ser
    except serial.SerialException as e:
        print(f"오류: 시리얼 포트를 열 수 없습니다. '{SERIAL_PORT}'. {e}")
        print("1) 장치 연결 확인  2) 포트 이름 확인  3) 다른 프로그램이 포트 사용 중인지 확인")
        return None

def parse_pressure_values(line):
    """압력 값들을 파싱하여 읽기 쉬운 형태로 반환"""
    try:
        parts = line.split(',')
        if len(parts) >= 12:  # timestamp + 11개 센서 값
            timestamp = parts[0]
            pressure_values = parts[1:12]  # 11개 값 모두 사용
            # 압력 값들을 정수로 변환하여 포맷팅
            formatted_values = []
            for i, val in enumerate(pressure_values, 1):
                try:
                    pressure = int(val.strip())
                    formatted_values.append(f"S{i}:{pressure:4d}")
                except ValueError:
                    formatted_values.append(f"S{i}: N/A")
            return timestamp, formatted_values
        return None, None
    except Exception:
        return None, None

def nonblocking_readline_win(input_buffer):
    """
    Windows 콘솔에서 비차단으로 키 입력을 모아 한 줄(엔터) 단위로 반환.
    - 숫자/백스페이스/엔터/'q' 처리
    반환값:
      - (line, quit_flag)
      - line: 엔터로 확정된 문자열(없으면 None)
      - quit_flag: 'q'가 입력되면 True
    """
    line = None
    quit_flag = False

    while msvcrt.kbhit():
        ch = msvcrt.getwch()  # 유니코드
        if ch in ('\r', '\n'):
            if input_buffer:
                line = input_buffer
                input_buffer = ""
            # CRLF 처리: 그대로 비움
        elif ch == '\x08':  # Backspace
            input_buffer = input_buffer[:-1]
        elif ch.lower() == 'q':
            quit_flag = True
        else:
            # 숫자와 공백만 허용(원하면 +,- 등 추가 가능)
            if ch.isdigit() or ch.isspace():
                input_buffer += ch
            # 그 외 문자는 무시
    return line, quit_flag, input_buffer

def main():
    ser = setup_serial_connection()
    if ser is None:
        return

    # CSV 헤더 작성 (11개 센서에 맞게 수정)
    with open(OUTPUT_FILENAME, 'a', encoding='utf-8') as f:
        f.write("pose,timestamp_ms,s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11\n")
    print(f"데이터를 '{OUTPUT_FILENAME}'에 기록 중입니다. 중지: Ctrl+C 또는 콘솔에서 'q' 입력 후 엔터")
    print("자세 번호 입력 방법: 숫자 입력 후 엔터 → 5초 뒤 해당 번호로 라벨 변경")
    print("예) 2 <Enter>  → 5초 뒤부터 pose=2로 기록")
    print("-" * 80)

    current_pose = 0  # 기본 자세 번호
    pending_pose = None
    switch_at = None  # time.monotonic() 기준 스위치 예정 시각
    input_buffer = ""  # 키 입력 버퍼(Windows)

    try:
        while True:
            now = time.monotonic()

            # (1) 콘솔 입력 처리: 숫자 라인 확정 시 5초 후 스케줄
            if WINDOWS:
                line_in, quit_flag, input_buffer = nonblocking_readline_win(input_buffer)
                if quit_flag:
                    print("\n'q' 입력으로 종료합니다.")
                    break
                if line_in is not None:
                    try:
                        # 공백 제거 후 정수 해석
                        pose_num = int(line_in.strip())
                        pending_pose = pose_num
                        switch_at = now + 5.0
                        print(f"[입력확정] pose={pose_num} → 5초 뒤({5.0:.1f}s)부터 적용 예정")
                    except ValueError:
                        print(f"[무시] 숫자가 아닙니다: '{line_in}'")

            # (2) 스케줄된 자세 변경 적용
            if pending_pose is not None and switch_at is not None and now >= switch_at:
                current_pose = pending_pose
                print(f"[적용] 현재 pose={current_pose} 로 전환 완료")
                pending_pose = None
                switch_at = None

            # (3) 시리얼 수신 처리
            if ser.in_waiting > 0:
                try:
                    raw = ser.readline()
                    if not raw:
                        continue
                    line = raw.decode('utf-8', errors='replace').strip()
                except Exception as e:
                    print(f"[경고] 시리얼 디코딩 오류: {e}")
                    continue

                if line:
                    print(f"[원본 데이터] {line}")  # 디버깅용 원본 데이터 출력
                    
                    # 압력 값 파싱
                    timestamp, pressure_values = parse_pressure_values(line)
                    
                    # 콘솔 출력 (압력 값들을 보기 좋게 표시)
                    if pressure_values:
                        pressure_display = " | ".join(pressure_values)
                        if pending_pose is not None and switch_at is not None:
                            remaining = max(0.0, switch_at - now)
                            print(f"[Pose:{current_pose:2d}] [전환까지:{remaining:4.1f}s] {pressure_display}")
                        else:
                            print(f"[Pose:{current_pose:2d}] {pressure_display}")
                    else:
                        # 파싱 실패 시 원본 출력
                        if pending_pose is not None and switch_at is not None:
                            remaining = max(0.0, switch_at - now)
                            print(f"수신(pose={current_pose}, 전환까지 {remaining:0.1f}s): {line}")
                        else:
                            print(f"수신(pose={current_pose}): {line}")

                    # 파일 기록
                    record = f"{current_pose},{line}"
                    with open(OUTPUT_FILENAME, 'a', encoding='utf-8') as f:
                        f.write(record + '\n')

            # CPU 사용 억제 및 버퍼링 시간 확보
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n데이터 기록을 중지합니다.")
    except Exception as e:
        print(f"예외 발생: {e}")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("시리얼 포트가 닫혔습니다.")

if __name__ == "__main__":
    main()