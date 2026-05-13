from pathlib import Path
import pickle

import pandas as pd
import xgboost as xgb

from model.features import FEATURES

ROOT_DIR = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT_DIR / "dataset" / "almaty_aqi_dataset.csv"
MODEL_PATH = ROOT_DIR / "model" / "models" / "xgboost_model.pkl"


def main():
    df = pd.read_csv(DATASET_PATH, parse_dates=["time"])
    data = df[FEATURES + ["target_aqi_1h"]].dropna()

    X = data[FEATURES]
    y = data["target_aqi_1h"]

    model = xgb.XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        objective="reg:squarederror",
        random_state=42,
    )

    model.fit(X, y)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"model": model, "features": FEATURES}, f)

    print(f"MODEL SAVED: {MODEL_PATH}")
    print(f"Training rows: {len(data)}")
    print(f"Features: {len(FEATURES)}")


if __name__ == "__main__":
    main()