# ============================================================
# formatter.py | CAT_bot
# Формування текстів повідомлень для Telegram (простий текст)
# ============================================================

from datetime import date


def weekly_report(state):
    """
    Функція формування тижневого звіту для Telegram.
    Надсилається щонеділі о 00:00 (Київ).
    state — поточний словник стану бота
    """
    today     = date.today().strftime("%d.%m.%Y")
    week_num  = state["week_number"]
    year      = state["season_year"]
    sat_a     = state["sat_apple_week"]
    sat_g     = state["sat_grape_week"]
    precip    = state["precip_week"]
    sat_a_s   = state["sat_apple_season"]
    sat_g_s   = state["sat_grape_season"]
    precip_s  = state["precip_season"]
    frost_cnt = state["frost_count"]

    # Залишок до сезонної цілі (не може бути від'ємним)
    left_apple = max(0.0, 2000 - sat_a_s)
    left_grape = max(0.0, 3000 - sat_g_s)

    lines = [
        "CAT_bot | Тижневий звіт",
        f"Дата: {today}  |  Сезон {year}  |  Тиждень {week_num}",
        "",
        "=== ЗА ТИЖДЕНЬ ===",
        f"САТ яблуня  (+5C):  {sat_a:.1f} C",
        f"САТ виноград (+10C): {sat_g:.1f} C",
        f"Опади:              {precip:.1f} мм",
        "",
        "=== ЗА СЕЗОН ===",
        f"САТ яблуня:   {sat_a_s:.1f} C  (залишок {left_apple:.0f} C до 2000)",
        f"САТ виноград: {sat_g_s:.1f} C  (залишок {left_grape:.0f} C до 3000)",
        f"Опади:        {precip_s:.1f} мм",
        f"Заморозків:   {frost_cnt} раз(и)",
    ]
    return "\n".join(lines)


def frost_warning(temp, forecast):
    """
    Функція формування попередження про заморозок.
    temp     — поточна температура (°C)
    forecast — словник {min_temp, min_time} з прогнозу на 24 год
    """
    min_t  = forecast["min_temp"] if forecast else temp
    min_tm = forecast["min_time"][11:16] if forecast else "--:--"

    lines = [
        "CAT_bot | УВАГА: ЗАМОРОЗОК",
        f"Зараз:   {temp:.1f} C",
        f"Прогноз мінімум: {min_t:.1f} C о {min_tm}",
        "",
        "Яблуня:   критично при -2C (цвітіння)",
        "Виноград: критично при -1C (молоді пагони)",
        "Вживайте захисних заходів!",
    ]
    return "\n".join(lines)