from datetime import datetime, timedelta
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from model.features import FEATURES, build_features

app = FastAPI(title="Almaty AQI API", version="3.1.0")

model = None
model_features = None


class PredictRequest(BaseModel):
    datetime_str: str


def resolve_model_path() -> Path:
    candidates = [
        Path("/app/model/models/xgboost_model.pkl"),
        Path(__file__).resolve().parents[1] / "model" / "models" / "xgboost_model.pkl",
    ]

    for path in candidates:
        if path.exists():
            return path

    raise RuntimeError(
        "Model not found. Expected xgboost_model.pkl in /app/model/models/ "
        "or project model/models/."
    )


@app.on_event("startup")
def load_model():
    global model, model_features

    model_path = resolve_model_path()

    with open(model_path, "rb") as f:
        data = pickle.load(f)

    model = data["model"]
    model_features = data.get("features", FEATURES)

    print("Model loaded:", model_path)
    print("Model type:", type(model))
    print("Features:", len(model_features))


def parse_datetime(dt_str: str) -> datetime:
    """Support 'YYYY-MM-DD HH:MM' and 'HH:MM'."""
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            return datetime.strptime(f"{today} {dt_str}", "%Y-%m-%d %H:%M")
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="datetime_str must be in 'YYYY-MM-DD HH:MM' or 'HH:MM' format",
            ) from exc


def get_category(aqi: int):
    if aqi <= 50:
        return "Хороший", "#00e400"
    if aqi <= 100:
        return "Умеренный", "#ffff00"
    if aqi <= 150:
        return "Вредный для чувствительных", "#ff7e00"
    if aqi <= 200:
        return "Вредный", "#ff0000"
    if aqi <= 300:
        return "Очень вредный", "#8f3f97"
    return "Опасный", "#7e0023"


def get_advice(aqi: int) -> str:
    if aqi <= 50:
        return "Качество воздуха хорошее. Можно гулять и проветривать помещение."
    if aqi <= 100:
        return "Качество приемлемое. Чувствительным людям лучше снизить долгие нагрузки на улице."
    if aqi <= 150:
        return "Чувствительным группам стоит ограничить прогулки и активный спорт на улице."
    if aqi <= 200:
        return "Лучше сократить время на улице, закрыть окна и избегать интенсивных нагрузок."
    if aqi <= 300:
        return "Рекомендуется оставаться в помещении и использовать очиститель воздуха при наличии."
    return "Опасный уровень загрязнения. Избегайте выхода на улицу без необходимости."


def aqi_to_pm25(aqi: int) -> float:
    """Approximate PM2.5 concentration from US EPA AQI breakpoints."""
    breakpoints = [
        (0, 50, 0.0, 12.0),
        (51, 100, 12.1, 35.4),
        (101, 150, 35.5, 55.4),
        (151, 200, 55.5, 150.4),
        (201, 300, 150.5, 250.4),
        (301, 400, 250.5, 350.4),
        (401, 500, 350.5, 500.4),
    ]

    for i_low, i_high, c_low, c_high in breakpoints:
        if i_low <= aqi <= i_high:
            return round((c_high - c_low) / (i_high - i_low) * (aqi - i_low) + c_low, 1)
    return 500.4


def build_df(dt: datetime) -> pd.DataFrame:
    data = build_features(dt)
    df = pd.DataFrame([data])

    expected_features = model_features or FEATURES
    for feature in expected_features:
        if feature not in df.columns:
            df[feature] = 0.0

    return df[expected_features]


def predict_aqi(dt_str: str):
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")

    dt = parse_datetime(dt_str)
    df = build_df(dt)
    pred = model.predict(df)[0]
    aqi = int(max(0, min(500, round(float(pred)))))
    category, color = get_category(aqi)
    pm25 = aqi_to_pm25(aqi)

    return {
        "datetime": dt.strftime("%Y-%m-%d %H:%M"),
        "aqi": aqi,
        "category": category,
        "color": color,
        "pm25": pm25,
        "pm10": round(pm25 * 1.6, 1),
        "temperature": data_float(df, "temperature_2m"),
        "humidity": data_float(df, "relative_humidity_2m"),
        "wind_speed": data_float(df, "wind_speed_10m"),
        "pressure": data_float(df, "surface_pressure"),
        "advice": get_advice(aqi),
        "model_confidence": 0.85,
    }


def data_float(df: pd.DataFrame, column: str) -> float:
    if column not in df.columns:
        return 0.0
    return round(float(df.iloc[0][column]), 1)


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Almaty AQI API",
        "model_loaded": model is not None,
    }


@app.get("/current")
def current():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return predict_aqi(now)


@app.get("/history")
def history():
    now = datetime.now()
    labels, aqi_values, pm25_values = [], [], []

    for i in range(23, -1, -1):
        dt = now - timedelta(hours=i)
        res = predict_aqi(dt.strftime("%Y-%m-%d %H:%M"))

        labels.append(dt.strftime("%H:%M"))
        aqi_values.append(res["aqi"])
        pm25_values.append(res["pm25"])

    return {
        "labels": labels,
        "aqi_values": aqi_values,
        "pm25_values": pm25_values,
    }


@app.post("/predict")
def predict(req: PredictRequest):
    return predict_aqi(req.datetime_str)


@app.get("/debug-predict")
def debug():
    dt = datetime.now()
    df = build_df(dt)
    pred = model.predict(df)[0]

    return {
        "pred": float(pred),
        "min": float(np.min(df.values)),
        "max": float(np.max(df.values)),
        "shape": list(df.shape),
        "features": df.iloc[0].to_dict(),
    }