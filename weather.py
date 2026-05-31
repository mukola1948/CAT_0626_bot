# ============================================================
# weather.py | CAT_bot
# Отримання поточної погоди з Open-Meteo API (без ключа, безкоштовно)
# ============================================================

import requests
from config import LATITUDE, LONGITUDE

# Адреса API поточного прогнозу Open-Meteo
URL = "https://api.open-meteo.com/v1/forecast"


def get_weather():
    """
    Функція запиту поточної погоди.
    Повертає словник {temperature, precipitation} або None при помилці.
    temperature  — температура повітря на висоті 2 м (°C)
    precipitation — опади за останню годину (мм)
    """
    params = {
        "latitude":  LATITUDE,
        "longitude": LONGITUDE,
        "current":   "temperature_2m,precipitation",
        "timezone":  "Europe/Kiev",
    }
    try:
        r = requests.get(URL, params=params, timeout=15)
        r.raise_for_status()
        cur = r.json().get("current", {})
        return {
            "temperature":   cur.get("temperature_2m"),
            "precipitation": cur.get("precipitation", 0.0),
        }
    except Exception as e:
        print(f"Помилка weather API: {e}")
        return None


def get_frost_forecast():
    """
    Функція перевірки прогнозу заморозків на найближчі 24 години.
    Повертає словник {min_temp, min_time} або None при помилці.
    min_temp — мінімальна прогнозна температура за 24 год (°C)
    min_time — час настання мінімуму (рядок ISO)
    """
    params = {
        "latitude":     LATITUDE,
        "longitude":    LONGITUDE,
        "hourly":       "temperature_2m",
        "timezone":     "Europe/Kiev",
        "forecast_days": 2,
    }
    try:
        r = requests.get(URL, params=params, timeout=15)
        r.raise_for_status()
        hourly = r.json().get("hourly", {})
        temps  = hourly.get("temperature_2m", [])[:24]
        times  = hourly.get("time", [])[:24]
        if not temps:
            return None
        idx = temps.index(min(temps))
        return {"min_temp": temps[idx], "min_time": times[idx]}
    except Exception as e:
        print(f"Помилка frost forecast: {e}")
        return None