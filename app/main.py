"""
app/main.py — FastAPI заглушка для AQI Almaty
Возвращает фиктивные данные пока нет реальной модели.
Потом просто заменишь логику в /predict на реальную модель.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import random
import math

app = FastAPI(title="Almaty AQI API", version="1.0.0")

# ── Schemas ───────────────────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    datetime_str: str   # "2024-01-15 14:00"

class AQIResponse(BaseModel):
    datetime_str: str
    aqi: int
    category: str
    color: str
    pm25: float
    pm10: float
    temperature: float
    humidity: float
    advice: str

class HistoryResponse(BaseModel):
    labels: list[str]
    aqi_values: list[int]
    pm25_values: list[float]

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_category(aqi: int) -> tuple[str, str]:
    if aqi <= 50:
        return "Хороший", "#00e400"
    elif aqi <= 100:
        return "Умеренный", "#ffff00"
    elif aqi <= 150:
        return "Вредный для чувствительных", "#ff7e00"
    elif aqi <= 200:
        return "Вредный", "#ff0000"
    elif aqi <= 300:
        return "Очень вредный", "#8f3f97"
    else:
        return "Опасный", "#7e0023"

def get_advice(category: str) -> str:
    advice_map = {
        "Хороший": "Отличный день для прогулки! Воздух чистый.",
        "Умеренный": "Воздух приемлемый. Чувствительным людям стоит ограничить время на улице.",
        "Вредный для чувствительных": "Дети и пожилые люди должны ограничить активность на улице.",
        "Вредный": "Всем рекомендуется ограничить время на улице. Носите маску.",
        "Очень вредный": "Избегайте пребывания на улице. Держите окна закрытыми.",
        "Опасный": "Чрезвычайная ситуация! Оставайтесь дома.",
    }
    return advice_map.get(category, "")

def simulate_aqi(dt: datetime) -> int:
    """
    Заглушка — имитирует реалистичный AQI для Алматы.
    Зимой хуже, летом лучше. Утром и вечером хуже (пробки).
    ПОТОМ ЗАМЕНИТЬ НА РЕАЛЬНУЮ МОДЕЛЬ.
    """
    # Сезонность: зима хуже
    season_factor = 80 + 60 * math.cos((dt.month - 7) * math.pi / 6)
    # Суточный паттерн: утренний и вечерний пик
    hour_factor = 30 * math.exp(-((dt.hour - 8) ** 2) / 8) + \
                  25 * math.exp(-((dt.hour - 18) ** 2) / 8)
    # Случайный шум
    noise = random.gauss(0, 15)
    aqi = int(max(10, season_factor + hour_factor + noise))
    return min(aqi, 400)

# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Almaty AQI API is running"}

@app.post("/predict", response_model=AQIResponse)
def predict(req: PredictRequest):
    dt = datetime.strptime(req.datetime_str, "%Y-%m-%d %H:%M")
    aqi = simulate_aqi(dt)
    category, color = get_category(aqi)

    return AQIResponse(
        datetime_str=req.datetime_str,
        aqi=aqi,
        category=category,
        color=color,
        pm25=round(aqi * 0.42 + random.gauss(0, 3), 1),
        pm10=round(aqi * 0.65 + random.gauss(0, 5), 1),
        temperature=round(random.uniform(-10, 30), 1),
        humidity=round(random.uniform(30, 80), 1),
        advice=get_advice(category),
    )

@app.get("/history", response_model=HistoryResponse)
def history():
    """Последние 24 часа — для графика на главной странице."""
    now = datetime.now()
    labels, aqi_values, pm25_values = [], [], []

    for h in range(23, -1, -1):
        from datetime import timedelta
        dt = now - timedelta(hours=h)
        aqi = simulate_aqi(dt)
        labels.append(dt.strftime("%H:%M"))
        aqi_values.append(aqi)
        pm25_values.append(round(aqi * 0.42 + random.gauss(0, 2), 1))

    return HistoryResponse(
        labels=labels,
        aqi_values=aqi_values,
        pm25_values=pm25_values,
    )

@app.get("/current", response_model=AQIResponse)
def current():
    """Текущее состояние воздуха."""
    now = datetime.now()
    return predict(PredictRequest(datetime_str=now.strftime("%Y-%m-%d %H:%M")))