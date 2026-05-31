# ============================================================
# main.py | CAT_bot
# Головний файл — виконується кожні 2 год через GitHub Actions
# ============================================================

import requests
from datetime import datetime, date
from config import BOT_TOKEN, CHAT_ID, FROST_THR, SEASON_START_MONTH, SEASON_END_MONTH
from weather import get_weather, get_frost_forecast
from calculator import apple_contribution, grape_contribution
from state import load, save
from formatter import weekly_report, frost_warning


# ── Допоміжні функції ────────────────────────────────────────

def send(text):
    """
    Функція надсилання текстового повідомлення у Telegram.
    Використовує простий текст без HTML/Markdown щоб уникнути
    тихих помилок Telegram API при спеціальних символах.
    """
    if not BOT_TOKEN or not CHAT_ID:
        print("TELEGRAM_BOT_TOKEN або TELEGRAM_CHAT_ID не задані!")
        return
    url  = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    try:
        r = requests.post(url, json=data, timeout=10)
        r.raise_for_status()
        print("Telegram: надіслано успішно")
    except Exception as e:
        print(f"Помилка Telegram: {e}")


def is_season_active():
    """
    Перевірка чи поточний місяць входить в активний сезон.
    Поза сезоном (листопад–лютий) накопичення не виконується.
    """
    return SEASON_START_MONTH <= date.today().month <= SEASON_END_MONTH


def is_new_season(state):
    """
    Перевірка чи розпочався новий календарний сезон (новий рік).
    Якщо рік у state.json відрізняється від поточного — скидаємо сезонні лічильники.
    """
    return state["season_year"] != date.today().year


def reset_season(state):
    """
    Функція скидання всіх накопичувачів на початку нового сезону.
    Викликається один раз на початку кожного нового року.
    """
    state["season_year"]      = date.today().year
    state["sat_apple_season"] = 0.0
    state["sat_grape_season"] = 0.0
    state["precip_season"]    = 0.0
    state["sat_apple_week"]   = 0.0
    state["sat_grape_week"]   = 0.0
    state["precip_week"]      = 0.0
    state["week_number"]      = 1
    state["week_start_date"]  = str(date.today())
    state["frost_count"]      = 0
    state["last_frost_alert"] = None
    state["report_sent_week"] = None
    print("Новий сезон — всі лічильники скинуто")


def should_send_weekly_report(state):
    """
    Перевірка чи потрібно надіслати тижневий звіт зараз.
    Умова: сьогодні неділя І звіт за цей тиждень ще не надсилався.
    Захист від дублювання: поле report_sent_week зберігає номер тижня.
    """
    today = date.today()
    is_sunday      = today.weekday() == 6          # 6 = неділя в Python
    already_sent   = (state.get("report_sent_week") == state["week_number"])
    return is_sunday and not already_sent


def reset_weekly(state):
    """
    Функція скидання тижневих накопичувачів після надсилання звіту.
    Сезонні накопичувачі НЕ скидаються — тільки тижневі.
    """
    state["sat_apple_week"]  = 0.0
    state["sat_grape_week"]  = 0.0
    state["precip_week"]     = 0.0
    state["week_number"]    += 1
    state["week_start_date"] = str(date.today())
    print(f"Тиждень {state['week_number'] - 1} закрито, починається тиждень {state['week_number']}")


def handle_frost(temp, state):
    """
    Функція перевірки та обробки заморозку.
    Надсилає попередження не частіше одного разу на добу
    (захист від багаторазових сповіщень за одну ніч).
    temp  — поточна температура (°C)
    state — поточний стан бота
    """
    today_str = str(date.today())
    # Якщо попередження вже надсилалось сьогодні — пропускаємо
    if state.get("last_frost_alert") == today_str:
        print("Заморозок: попередження вже надіслане сьогодні")
        return
    forecast = get_frost_forecast()
    msg      = frost_warning(temp, forecast)
    send(msg)
    state["last_frost_alert"] = today_str
    state["frost_count"]      = state.get("frost_count", 0) + 1
    print(f"Заморозок {temp:.1f}C — попередження надіслано")


# ── Головна функція ───────────────────────────────────────────

def main():
    """
    Головна функція CAT_bot.
    Логіка виконання за кожен запуск (кожні 2 год):
      1. Завантажити стан
      2. Перевірити новий сезон
      3. Перевірити активність сезону
      4. Отримати погоду
      5. Перевірити заморозок → надіслати попередження якщо є
      6. Накопичити САТ та опади (тижневі + сезонні)
      7. Перевірити чи неділя → надіслати звіт і скинути тижневі лічильники
      8. Зберегти стан
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"CAT_bot запуск: {now}")

    # Крок 1: завантаження збереженого стану
    state = load()

    # Крок 2: перевірка нового сезону
    if is_new_season(state):
        reset_season(state)

    # Крок 3: перевірка активності сезону
    if not is_season_active():
        print("Поза сезоном (листопад–лютий). Накопичення призупинено.")
        save(state)
        return

    # Крок 4: отримання поточної погоди
    weather = get_weather()
    if not weather:
        print("Не вдалося отримати погоду — завершення без змін")
        return

    temp   = weather["temperature"]
    precip = weather["precipitation"]
    print(f"Температура: {temp}C  |  Опади: {precip} мм")

    # Крок 5: перевірка заморозку
    if temp is not None and temp <= FROST_THR:
        handle_frost(temp, state)

    # Крок 6: накопичення САТ та опадів
    add_apple = apple_contribution(temp)   # внесок яблуня за 2 год
    add_grape = grape_contribution(temp)   # внесок виноград за 2 год

    state["sat_apple_season"] = round(state["sat_apple_season"] + add_apple, 2)
    state["sat_grape_season"] = round(state["sat_grape_season"] + add_grape, 2)
    state["precip_season"]    = round(state["precip_season"]    + precip,    2)

    state["sat_apple_week"]   = round(state["sat_apple_week"]   + add_apple, 2)
    state["sat_grape_week"]   = round(state["sat_grape_week"]   + add_grape, 2)
    state["precip_week"]      = round(state["precip_week"]      + precip,    2)

    state["last_update"] = now
    print(f"Додано яблуня: +{add_apple:.4f}  виноград: +{add_grape:.4f}  опади: +{precip}")

    # Крок 7: перевірка недільного звіту
    if should_send_weekly_report(state):
        msg = weekly_report(state)
        send(msg)
        state["report_sent_week"] = state["week_number"]  # захист від дублів
        reset_weekly(state)

    # Крок 8: збереження стану
    save(state)
    print("Стан збережено. Завершення.")


if __name__ == "__main__":
    main()