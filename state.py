# ============================================================
# state.py | CAT_0626_bot
# Читання і запис стану бота у файл state.json
# Додані поля: денна статистика температур, статистика за період
# ============================================================

import json
import os
from datetime import date

STATE_FILE = "state.json"

DEFAULT = {
    "season_year":      date.today().year,
    "last_update":      None,

    # --- Сезонні накопичувачі (не скидаються до кінця сезону) ---
    "sat_apple_season": 0.0,   # САТ яблуні за сезон (°C)
    "sat_grape_season": 0.0,   # САТ винограду за сезон (°C)
    "precip_season":    0.0,   # опади за сезон (мм)

    # Температурна статистика за сезон (список денних stats-словників)
    # Кожен елемент: {date, tmin, tmax, tday, tnight}
    "season_daily_stats": [],

    # Заморозки за сезон: список {date, tmin}
    "frost_events": [],

    # --- Накопичувачі поточного звітного періоду ---
    # Скидаються після кожного підсумкового звіту
    "sat_apple_period": 0.0,
    "sat_grape_period": 0.0,
    "precip_period":    0.0,
    "period_start_date": str(date.today()),  # дата початку поточного періоду
    "period_daily_stats": [],               # денні stats за поточний період

    # Захист від дублювання підсумкового звіту
    "period_report_sent_date": None,  # дата коли надіслано останній підсумковий звіт

    # --- Денні накопичувачі (скидаються щодня після щоденного звіту) ---
    "today_date":         str(date.today()),
    "today_apple":        0.0,   # САТ яблуня за сьогодні (°C)
    "today_grape":        0.0,   # САТ виноград за сьогодні (°C)
    "today_precip":       0.0,   # опади за сьогодні (мм)
    "daily_report_sent":  None,  # дата надсилання щоденного звіту (захист від дублів)

    # Лічильник заморозків (залишено для сумісності)
    "frost_count": 0,
    "last_frost_alert": None,
}


def load():
    """
    Завантаження стану з state.json.
    При відсутності файлу або помилці — повертає DEFAULT.
    Відсутні ключі доповнюються з DEFAULT (захист при оновленні бота).
    """
    if not os.path.exists(STATE_FILE):
        return DEFAULT.copy()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        merged = DEFAULT.copy()
        merged.update(saved)
        return merged
    except Exception as e:
        print(f"Помилка читання state.json: {e}")
        return DEFAULT.copy()


def save(state):
    """
    Збереження поточного стану у state.json.
    """
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Помилка збереження state.json: {e}")