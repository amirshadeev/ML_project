# Almaty AQI Forecast

ML-система для прогноза качества воздуха в Алматы. Пользователь выбирает дату и время, а приложение возвращает прогноз AQI, категорию качества воздуха, рекомендации и дополнительные погодные параметры.

## Архитектура

```text
Streamlit frontend -> FastAPI API -> XGBoost model
```

В проекте оставлен один основной backend-сервис: `app/main.py` и frontend на Streamlit. 

## Структура

```text
app/                 FastAPI API
frontend/            Streamlit UI
model/features.py    Список признаков и генерация признаков для прогноза
model/train_model.py Обучение XGBoost модели
dataset/             Исходные CSV и подготовленный датасет
model/models/        Сохраненные модели и результаты
```

## Запуск через Docker


docker compose up --build

После запуска:

- Frontend: http://localhost:8501
- API: http://localhost:8000
- Debug prediction: http://localhost:8000/debug-predict

## Обучение модели локально

```bash
pip install -r requirements.api.txt
python -m model.train_model
```

Модель сохранится в `model/models/xgboost_model.pkl`.

## Важное ограничение

Текущий интерфейс принимает только дату и время. Модель обучена на более богатых признаках: история PM2.5, PM1, UM003 и погода. Поэтому `model/features.py` пока использует demo-значения для этих признаков.

Чтобы прогноз стал ближе к реальному production-варианту, нужно заменить demo-значения на:

- последние измерения PM2.5/PM1/UM003;
- прогноз погоды для выбранного времени;
- rolling/lag признаки, рассчитанные из актуальной истории измерений.