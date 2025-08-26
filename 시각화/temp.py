import os

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.neighbors import KNeighborsClassifier

# 데이터 폴더 및 라벨
pressure_dir = "./압력"
imu_dir = "./IMU"
posture_labels = ["0번자세", "1번자세", "2번자세", "4번자세"]

data_list = []

for posture in posture_labels:
    label = int(posture.replace("번자세", ""))
    pressure_path = os.path.join(pressure_dir, f"{posture}.csv")
    imu_path = os.path.join(imu_dir, f"{posture}.csv")

    pressure_df = pd.read_csv(pressure_path)
    imu_df = pd.read_csv(imu_path)

    pressure_df["pitch"] = imu_df["relative_pitch_deg"]
    pressure_df["label"] = label

    data_list.append(pressure_df)

all_data = pd.concat(data_list, ignore_index=True)

# 결측치 제거
all_data = all_data.dropna()

X = all_data.drop(columns=["label"])
y = all_data["label"]

# train/test 분리
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

knn = KNeighborsClassifier()

param_grid = {
    "n_neighbors": [3, 5, 7, 9],
    "weights": ["uniform", "distance"],
    "p": [1, 2],
}

grid_search = GridSearchCV(
    knn, param_grid, cv=5, n_jobs=-1, verbose=2, scoring="accuracy"
)
grid_search.fit(X_train, y_train)

print("최적 하이퍼파라미터:", grid_search.best_params_)
print(f"최고 교차검증 정확도: {grid_search.best_score_:.4f}")

best_knn = grid_search.best_estimator_
y_pred = best_knn.predict(X_test)

print("테스트 세트 평가 결과:")
print(classification_report(y_test, y_pred))
print(f"테스트 정확도: {accuracy_score(y_test, y_pred):.4f}")
