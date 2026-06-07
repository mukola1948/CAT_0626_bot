# ============================================================
# weather.py | CAT_0626_bot
# Отримання погодних даних з Open-Meteo API
# - поточна температура для накопичення САТ
# - погодинні дані за вчора для щоденного звіту
# - опади за останні 2 години
# - прогноз заморозків на 24 год
# ============================================================

import requests
from datetime import datetime, timedelta
from config import LATITUDE, LONGITUDE

URL = "https://api.open-meteo.com/v1/forecast"


def get_weather():
    """
    Поточна температура і сума опадів за останні 2 години.
    Повертає {temperature, precipitation} або None при помилці.
    """
    params = {
        "latitude":     LATITUDE,
        "longitude":    LONGITUDE,
        "current":      "temperature_2m",
        "hourly":       "precipitation",
        "timezone":     "Europe/Kiev",
        "forecast_days": 1,
        "past_hours":   3,
    }
    try:
        r = requests.get(URL, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        temp = data["current"]["temperature_2m"]

        # Сума опадів за останні 2 години
        hourly_times  = data["hourly"]["time"]
        hourly_precip = data["hourly"]["precipitation"]
        now = datetime.now()
        cur = now.replace(minute=0, second=0, microsecond=0)
        prv = cur - timedelta(hours=1)
        targets = {cur.strftime("%Y-%m-%dT%H:%M"), prv.strftime("%Y-%m-%dT%H:%M")}
        precip = sum(
            (hourly_precip[i] or 0.0)
            for i, t in enumerate(hourly_times) if t in targets
        )
        return {"temperature": temp, "precipitation": round(precip, 2)}

    except Exception as e:
        print(f"Помилка weather API: {e}")
        return None


def get_yesterday_hourly():
    """
    Погодинні температури за вчорашній день (24 значення).
    Використовується для розрахунку Tmin/Tmax/Tніч/Tдень щоденного звіту.
    Повертає {temps: [...], precip_sum: float} або None при помилці.
    temps      — список з 24 температур по годинах (°C)
    precip_sum — сума опадів за вчора (мм)
    """
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    params = {
        "latitude":   LATITUDE,
        "longitude":  LONGITUDE,
        "hourly":     "temperature_2m,precipitation",
        "timezone":   "Europe/Kiev",
        "start_date": yesterday,
        "end_date":   yesterday,
    }
    try:
        r = requests.get(URL, params=params, timeout=15)
        r.raise_for_status()
        hourly = r.json().get("hourly", {})
        temps  = hourly.get("temperature_2m", [])
        precip = hourly.get("precipitation", [])
        if not temps:
            return None
        return {
            "temps":      temps,
            "precip_sum": round(sum(p or 0.0 for p in precip), 2),
        }
    except Exception as e:
        print(f"Помилка yesterday hourly: {e}")
        return None


def get_frost_forecast():
    """
    Мінімальна прогнозна температура на найближчі 24 години.
    Повертає {min_temp, min_time} або None при помилці.
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