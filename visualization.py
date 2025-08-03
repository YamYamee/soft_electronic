import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib as mpl
from matplotlib import font_manager as fm

# 🧩 한글 폰트 설정 (맑은 고딕)
font_path = "C:\\Windows\\Fonts\\malgun.ttf"  # Windows 전용 경로
font_name = fm.FontProperties(fname=font_path).get_name()
mpl.rcParams['font.family'] = font_name
mpl.rcParams['axes.unicode_minus'] = False

# 📁 데이터 디렉토리 설정
pressure_dir = "./압력"
imu_dir = "./IMU"
posture_labels = ["0번자세", "1번자세", "2번자세", "4번자세"]

# 📊 데이터 불러오기 및 통합
data_list = []
for posture in posture_labels:
    label = int(posture.replace("번자세", ""))
    pressure_path = os.path.join(pressure_dir, f"{posture}.csv")
    imu_path = os.path.join(imu_dir, f"{posture}.csv")

    pressure_df = pd.read_csv(pressure_path)
    imu_df = pd.read_csv(imu_path)

    pressure_df['pitch'] = imu_df['relative_pitch_deg']
    pressure_df['label'] = label
    pressure_df['timestamp'] = imu_df['timestamp_ms']

    data_list.append(pressure_df)

all_data = pd.concat(data_list, ignore_index=True).dropna()

# ================================
# 1️⃣ 자세별 평균 압력 히트맵 저장
# ================================
avg_pressure = all_data.groupby('label')[[f'pv{i}' for i in range(1, 9)]].mean()

plt.figure(figsize=(10, 4))
sns.heatmap(avg_pressure, annot=True, cmap="coolwarm", fmt=".0f", cbar_kws={'label': '압력값'})
plt.title("자세별 평균 압력 센서 값 (pv1~pv8)")
plt.xlabel("센서")
plt.ylabel("자세 라벨")
plt.tight_layout()
plt.savefig("avg_pressure_heatmap.png")
plt.close()

# ================================
# 2️⃣ pitch 변화 시계열 그래프 저장
# ================================
plt.figure(figsize=(12, 5))
for label in all_data['label'].unique():
    subset = all_data[all_data['label'] == label].reset_index()
    plt.plot(subset['timestamp'], subset['pitch'], label=f'{label}번자세')

plt.title("자세별 Pitch 변화 (시간 기준)")
plt.xlabel("timestamp (ms)")
plt.ylabel("pitch (deg)")
plt.legend()
plt.tight_layout()
plt.savefig("pitch_timeseries.png")
plt.close()

# ================================
# 3️⃣ 자세별 pitch 분포 박스플롯 저장
# ================================
plt.figure(figsize=(8, 5))
sns.boxplot(data=all_data, x='label', y='pitch', palette='Set2')
plt.title("자세별 pitch 값 분포")
plt.xlabel("자세 라벨")
plt.ylabel("Pitch (deg)")
plt.tight_layout()
plt.savefig("pitch_boxplot.png")
plt.close()
