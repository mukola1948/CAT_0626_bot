# ============================================================
# main.py | CAT_0626_bot
# Головний файл — виконується кожні 2 год через GitHub Actions
#
# Розклад подій:
#   Кожні 2 год  — накопичення САТ, опадів, перевірка заморозку
#   Щодня о 12:00 Київ (09:00 UTC) — щоденний контрольний звіт
#   Debug: кожні 3 дні — підсумковий звіт
#   Робочий: 11-го, 21-го, 1-го числа — підсумковий звіт
# ============================================================

import requests
from datetime import datetime, date, timedelta
from config import (BOT_TOKEN, CHAT_ID, FROST_THR,
                    SEASON_START_MONTH, SEASON_END_MONTH,
                    DEBUG_MODE, DEBUG_INTERVAL, REPORT_DAYS)
from weather import get_weather, get_yesterday_hourly, get_frost_forecast
from calculator import apple_contribution, grape_contribution, calc_temp_stats, merge_temp_stats
from state import load, save
from formatter import daily_report, period_report, frost_warning


# ── Надсилання у Telegram ────────────────────────────────────

def send(text):
    """
    Надсилання текстового повідомлення у Telegram.
    """
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram токен або chat_id не задані!")
        return
    url  = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    try:
        r = requests.post(url, json=data, timeout=10)
        r.raise_for_status()
        print("Telegram: надіслано")
    except Exception as e:
        print(f"Помилка Telegram: {e}")


# ── Перевірки сезону ─────────────────────────────────────────

def is_season_active():
    """Чи поточний місяць входить в активний сезон (березень–жовтень)."""
    return SEASON_START_MONTH <= date.today().month <= SEASON_END_MONTH


def is_new_season(state):
    """Чи розпочався новий календарний рік — потрібно скинути сезон."""
    return state["season_year"] != date.today().year


def reset_season(state):
    """
    Скидання всіх накопичувачів на початку нового сезону.
    Викликається один раз на рік при першому запуску нового сезону.
    """
    today = date.today()
    state.update({
        "season_year":           today.year,
        "sat_apple_season":      0.0,
        "sat_grape_season":      0.0,
        "precip_season":         0.0,
        "season_daily_stats":    [],
        "frost_events":          [],
        "sat_apple_period":      0.0,
        "sat_grape_period":      0.0,
        "precip_period":         0.0,
        "period_start_date":     str(today),
        "period_daily_stats":    [],
        "period_report_sent_date": None,
        "today_date":            str(today),
        "today_apple":           0.0,
        "today_grape":           0.0,
        "today_precip":          0.0,
        "daily_report_sent":     None,
        "frost_count":           0,
        "last_frost_alert":      None,
    })
    print("Новий сезон — всі лічильники скинуто")


# ── Логіка нового дня ────────────────────────────────────────

def handle_new_day(state):
    """
    Перехід до нового дня: скидання денних лічильників.
    Викликається коли today_date у state відрізняється від поточної дати.
    """
    today_str = str(date.today())
    state["today_date"]   = today_str
    state["today_apple"]  = 0.0
    state["today_grape"]  = 0.0
    state["today_precip"] = 0.0
    print(f"Новий день: {today_str}")


# ── Щоденний контрольний звіт о 12:00 ───────────────────────

def should_send_daily_report(state):
    """
    Перевірка чи потрібно надіслати щоденний звіт.
    Умова: зараз між 09:00–11:00 UTC (12:00–14:00 Київ влітку)
    і звіт сьогодні ще не надсилався.
    """
    now = datetime.utcnow()
    in_window  = 9 <= now.hour < 11          # вікно надсилання о 12:00 Київ
    today_str  = str(date.today())
    not_sent   = state.get("daily_report_sent") != today_str
    return in_window and not_sent


def send_daily_report(state):
    """
    Формування і надсилання щоденного контрольного звіту.
    Бере погодинні дані за вчора і формує повідомлення.
    """
    yesterday     = date.today() - timedelta(days=1)
    yesterday_str = str(yesterday)

    # Отримання погодинних даних за вчора
    ydata = get_yesterday_hourly()
    if not ydata:
        print("Не вдалося отримати дані за вчора — щоденний звіт пропущено")
        return

    # Розрахунок температурної статистики за вчора
    ystats = calc_temp_stats(ydata["temps"])
    y_precip = ydata["precip_sum"]

    # Розрахунок денного внеску САТ на основі погодинних даних за вчора
    # Беремо середню температуру за вчора і рахуємо повний денний внесок
    valid_temps = [t for t in ydata["temps"] if t is not None]
    if valid_temps:
        avg_yesterday = sum(valid_temps) / len(valid_temps)
        y_apple = round(max(0.0, avg_yesterday - 5.0),  2)
        y_grape = round(max(0.0, avg_yesterday - 10.0), 2)
    else:
        y_apple = 0.0
        y_grape = 0.0

    # Збереження статистики вчорашнього дня у period_daily_stats і season_daily_stats
    if ystats:
        entry = {"date": yesterday_str, **ystats}
        if not any(d.get("date") == yesterday_str for d in state["period_daily_stats"]):
            state["period_daily_stats"].append(entry)
        if not any(d.get("date") == yesterday_str for d in state["season_daily_stats"]):
            state["season_daily_stats"].append(entry)

    # Підсумкова статистика за поточний період
    period_stats = merge_temp_stats(state["period_daily_stats"])
    season_stats = merge_temp_stats(state["season_daily_stats"])

    msg = daily_report(
        yesterday_str    = yesterday_str,
        yesterday_stats  = ystats,
        yesterday_apple  = y_apple,
        yesterday_grape  = y_grape,
        yesterday_precip = y_precip,
        period_start_str = state["period_start_date"],
        sat_apple_period = state["sat_apple_period"],
        sat_grape_period = state["sat_grape_period"],
        sat_apple_season = state["sat_apple_season"],
        sat_grape_season = state["sat_grape_season"],
    )
    send(msg)
    state["daily_report_sent"] = str(date.today())
    print("Щоденний звіт надіслано")


# ── Підсумковий звіт за період ───────────────────────────────

def should_send_period_report(state):
    """
    Перевірка чи потрібно надіслати підсумковий звіт за період.

    Debug-режим (DEBUG_MODE=True):
      звіт кожні DEBUG_INTERVAL днів від дати початку періоду.

    Робочий режим (DEBUG_MODE=False):
      звіт 11-го, 21-го і 1-го числа місяця.

    Захист від дублювання: period_report_sent_date зберігає дату надсилання.
    """
    today     = date.today()
    today_str = str(today)
    already_sent = state.get("period_report_sent_date") == today_str

    if already_sent:
        return False

    if DEBUG_MODE:
        period_start = date.fromisoformat(state["period_start_date"])
        days_elapsed = (today - period_start).days
        return days_elapsed >= DEBUG_INTERVAL

    # Робочий режим: 1-ше, 11-те, 21-ше число
    return today.day in REPORT_DAYS


def send_period_report(state):
    """
    Формування і надсилання підсумкового звіту за період.
    Після надсилання скидає лічильники поточного періоду.
    """
    today     = date.today()
    today_str = str(today)

    period_end_str = str(today - timedelta(days=1))

    # Статистика температур за період і сезон
    period_stats = merge_temp_stats(state.get("period_daily_stats", []))
    season_stats = merge_temp_stats(state.get("season_daily_stats", []))

    # Заморозки: усі за сезон і тільки за поточний період
    period_start = date.fromisoformat(state["period_start_date"])
    all_frosts   = state.get("frost_events", [])
    period_frosts = [
        e for e in all_frosts
        if date.fromisoformat(e["date"]) >= period_start
    ]

    msg = period_report(
        period_start_str    = state["period_start_date"],
        period_end_str      = period_end_str,
        period_stats        = period_stats,
        sat_apple_period    = state["sat_apple_period"],
        sat_grape_period    = state["sat_grape_period"],
        precip_period       = state["precip_period"],
        period_frost_events = period_frosts,
        season_stats        = season_stats,
        sat_apple_season    = state["sat_apple_season"],
        sat_grape_season    = state["sat_grape_season"],
        precip_season       = state["precip_season"],
        season_frost_events = all_frosts,
    )
    send(msg)

    # Скидання лічильників поточного періоду
    state["period_report_sent_date"] = today_str
    state["sat_apple_period"]   = 0.0
    state["sat_grape_period"]   = 0.0
    state["precip_period"]      = 0.0
    state["period_start_date"]  = today_str
    state["period_daily_stats"] = []
    print(f"Підсумковий звіт надіслано. Новий період з {today_str}")


# ── Заморозок ────────────────────────────────────────────────

def handle_frost(temp, state):
    """
    Перевірка і обробка заморозку.
    Надсилає попередження не частіше одного разу на добу.
    Записує подію у frost_events для звіту.
    """
    today_str = str(date.today())
    if state.get("last_frost_alert") == today_str:
        print("Заморозок: попередження вже надіслане сьогодні")
        return
    forecast = get_frost_forecast()
    msg      = frost_warning(temp, forecast)
    send(msg)

    # Запис події заморозку
    state.setdefault("frost_events", [])
    state["frost_events"].append({"date": today_str, "tmin": round(temp, 1)})
    state["last_frost_alert"] = today_str
    state["frost_count"]      = state.get("frost_count", 0) + 1
    print(f"Заморозок {temp:.1f}°C — попередження надіслано")


# ── Головна функція ───────────────────────────────────────────

def main():
    """
    Головна функція CAT_0626_bot.
    Виконується кожні 2 год через GitHub Actions cron.

    Порядок дій за кожен запуск:
    1. Завантажити стан
    2. Перевірити новий сезон → скинути якщо треба
    3. Перевірити активність сезону → вийти якщо поза сезоном
    4. Перевірити новий день → скинути денні лічильники
    5. Отримати погоду
    6. Перевірити заморозок → надіслати попередження
    7. Накопичити САТ та опади (денні + період + сезон)
    8. Перевірити щоденний звіт о 12:00 → надіслати якщо час
    9. Перевірити підсумковий звіт → надіслати якщо настав час
    10. Зберегти стан
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"CAT_0626_bot запуск: {now_str}")

    # 1. Завантаження стану
    state = load()

    # 2. Новий сезон
    if is_new_season(state):
        reset_season(state)

    # 3. Активність сезону
    if not is_season_active():
        print("Поза сезоном. Накопичення призупинено.")
        save(state)
        return

    # 4. Новий день
    today_str = str(date.today())
    if state.get("today_date") != today_str:
        handle_new_day(state)

    # 5. Отримання погоди
    weather = get_weather()
    if not weather:
        print("Не вдалося отримати погоду — завершення")
        return

    temp   = weather["temperature"]
    precip = weather["precipitation"]
    print(f"Температура: {temp}°C  |  Опади: {precip} мм")

    # 6. Заморозок
    if temp is not None and temp <= FROST_THR:
        handle_frost(temp, state)

    # 7. Накопичення САТ та опадів
    add_apple = apple_contribution(temp)
    add_grape = grape_contribution(temp)

    # Денні накопичувачі
    state["today_apple"]  = round(state["today_apple"]  + add_apple, 4)
    state["today_grape"]  = round(state["today_grape"]  + add_grape, 4)
    state["today_precip"] = round(state["today_precip"] + precip,    2)

    # Накопичувачі поточного звітного періоду
    state["sat_apple_period"] = round(state["sat_apple_period"] + add_apple, 2)
    state["sat_grape_period"] = round(state["sat_grape_period"] + add_grape, 2)
    state["precip_period"]    = round(state["precip_period"]    + precip,    2)

    # Сезонні накопичувачі
    state["sat_apple_season"] = round(state["sat_apple_season"] + add_apple, 2)
    state["sat_grape_season"] = round(state["sat_grape_season"] + add_grape, 2)
    state["precip_season"]    = round(state["precip_season"]    + precip,    2)

    state["last_update"] = now_str
    print(f"Додано — яблуня: +{add_apple:.4f}  виноград: +{add_grape:.4f}")

    # 8. Щоденний звіт о 12:00
    if should_send_daily_report(state):
        send_daily_report(state)

    # 9. Підсумковий звіт за період
    if should_send_period_report(state):
        send_period_report(state)

    # 10. Збереження стану
    save(state)
    print("Стан збережено. Завершення.")


if __name__ == "__main__":
    main()