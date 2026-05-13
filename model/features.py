from datetime import datetime

FEATURES = [
    "pm25_lag_1h", "pm25_lag_3h", "pm25_lag_6h", "pm25_lag_24h",
    "pm25_roll_mean_6h", "pm25_roll_mean_24h", "pm25_roll_std_6h",
    "pm1_value", "um003_value",
    "temperature_2m", "relative_humidity_2m", "precipitation",
    "surface_pressure", "wind_speed_10m", "wind_direction_10m",
    "hour", "day_of_week", "month",
    "is_weekend", "is_heating_season", "is_rush_hour",
]


def build_features(dt: datetime):
    """
    Build the feature row used by the model at inference time.

    The project currently accepts only date/time from the user, so pollutant lag
    and weather values are demo defaults. For a production forecast, replace
    these values with recent sensor readings and weather forecast data.
    """
    is_winter = dt.month in [10, 11, 12, 1, 2, 3, 4]

    return {
        "hour": dt.hour,
        "day_of_week": dt.weekday(),
        "month": dt.month,
        "is_weekend": int(dt.weekday() >= 5),
        "is_heating_season": int(is_winter),
        "is_rush_hour": int(dt.hour in [7, 8, 9, 17, 18, 19]),

        # Demo defaults. Keep these aligned with the training feature names.
        "pm25_lag_1h": 50.0,
        "pm25_lag_3h": 48.0,
        "pm25_lag_6h": 45.0,
        "pm25_lag_24h": 40.0,
        "pm25_roll_mean_6h": 48.0,
        "pm25_roll_mean_24h": 45.0,
        "pm25_roll_std_6h": 12.0,
        "pm1_value": 35.0,
        "um003_value": 42.0,
        "temperature_2m": -5.0 if is_winter else 20.0,
        "relative_humidity_2m": 70.0 if is_winter else 55.0,
        "precipitation": 0.0,
        "surface_pressure": 950.0,
        "wind_speed_10m": 3.0,
        "wind_direction_10m": 180.0,
    }