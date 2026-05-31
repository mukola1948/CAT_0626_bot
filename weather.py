# ============================================================
# weather.py | CAT_0626_bot
# Отримання поточної погоди з Open-Meteo API (без ключа, безкоштовно)
# Опади: сума за останні 2 години (між запусками бота)
# ============================================================

import requests
from datetime import datetime, timedelta
from config import LATITUDE, LONGITUDE

URL = "https://api.open-meteo.com/v1/forecast"


def get_weather():
    """
    Функція запиту поточної температури та суми опадів за останні 2 години.
    Повертає словник {temperature, precipitation} або None при помилці.
    temperature   — температура повітря на висоті 2 м (°C)
    precipitation — сума опадів за останні 2 години (мм) — правильний метод
    """
    params = {
        "latitude":     LATITUDE,
        "longitude":    LONGITUDE,
        "current":      "temperature_2m",
        "hourly":       "precipitation",
        "timezone":     "Europe/Kiev",
        "forecast_days": 1,
        "past_hours":   3,   # запитуємо 3 години назад щоб гарантовано мати 2
    }
    try:
        r = requests.get(URL, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        # Поточна температура з блоку current (найточніший метод)
        temp = data["current"]["temperature_2m"]

        # Сума опадів за останні 2 години з погодинного масиву
        hourly_times  = data["hourly"]["time"]
        hourly_precip = data["hourly"]["precipitation"]

        # Знаходимо поточну годину і беремо дві останні записи
        now = datetime.now()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        prev_hour    = current_hour - timedelta(hours=1)

        # Форматуємо для порівняння з рядками API (формат: "2026-05-31T14:00")
        target_hours = [
            prev_hour.strftime("%Y-%m-%dT%H:%M"),
            current_hour.strftime("%Y-%m-%dT%H:%M"),
        ]

        # Підсумовуємо опади за знайдені години
        precip_sum = 0.0
        for i, t in enumerate(hourly_times):
            if t in target_hours:
                precip_sum += hourly_precip[i] or 0.0

        return {
            "temperature":   temp,
            "precipitation": round(precip_sum, 2),
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
        "latitude":      LATITUDE,
        "longitude":     LONGITUDE,
        "hourly":        "temperature_2m",
        "timezone":      "Europe/Kiev",
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