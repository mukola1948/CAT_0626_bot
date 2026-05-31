# ============================================================
# state.py | CAT_bot
# Читання і запис стану бота у файл state.json
# Зберігаються лише числа — жодних масивів сирих даних
# ============================================================

import json
import os
from datetime import date

STATE_FILE = "state.json"

# Шаблон порожнього стану на початок сезону
DEFAULT = {
    "season_year":      date.today().year,  # рік поточного сезону
    "last_update":      None,               # час останнього запуску (ISO рядок)

    # Сезонні накопичувачі (не скидаються до кінця сезону)
    "sat_apple_season": 0.0,   # сума активних температур яблуні за сезон (°C)
    "sat_grape_season": 0.0,   # сума активних температур винограду за сезон (°C)
    "precip_season":    0.0,   # загальні опади за сезон (мм)

    # Тижневі накопичувачі (скидаються після кожного недільного звіту)
    "sat_apple_week":   0.0,   # САТ яблуні за поточний тиждень (°C)
    "sat_grape_week":   0.0,   # САТ винограду за поточний тиждень (°C)
    "precip_week":      0.0,   # опади за поточний тиждень (мм)

    # Мета-дані тижня
    "week_number":      1,            # порядковий номер тижня сезону
    "week_start_date":  str(date.today()),  # дата початку поточного тижня

    # Лічильник заморозків і захист від дублювання попереджень
    "frost_count":      0,     # кількість виявлених заморозків за сезон
    "last_frost_alert": None,  # дата останнього надісланого попередження (рядок)
    "report_sent_week": None,  # номер тижня для якого вже надіслано звіт (захист від дублів)
}


def load():
    """
    Функція завантаження стану з файлу state.json.
    Якщо файл відсутній або пошкоджений — повертає DEFAULT.
    """
    if not os.path.exists(STATE_FILE):
        return DEFAULT.copy()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        # Доповнюємо відсутні ключі з DEFAULT (захист при оновленні бота)
        merged = DEFAULT.copy()
        merged.update(saved)
        return merged
    except Exception as e:
        print(f"Помилка читання state.json: {e}")
        return DEFAULT.copy()


def save(state):
    """
    Функція збереження поточного стану у файл state.json.
    """
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Помилка збереження state.json: {e}")