# ============================================================
# formatter.py | CAT_0626_bot
# Формування текстів Telegram-повідомлень
# Формат чисел: кома як десятковий розділювач (українська традиція)
# ============================================================

from datetime import date, timedelta


def _f(val):
    """
    Форматування числа з комою замість крапки.
    Наприклад: 19.8 → '19,8'
    """
    if val is None:
        return "н/д"
    return f"{val:.1f}".replace(".", ",")


def _frost_line(frost_events):
    """
    Рядок заморозків для звіту.
    frost_events — список словників {date, tmin} за сезон або період.
    Якщо заморозків не було — повертає '---'
    """
    if not frost_events:
        return "---"
    parts = [f"{e['date']} Tmin {_f(e['tmin'])}°C" for e in frost_events]
    return ", ".join(parts)


def daily_report(yesterday_str, yesterday_stats, yesterday_apple,
                 yesterday_grape, yesterday_precip,
                 period_start_str, sat_apple_period, sat_grape_period,
                 sat_apple_season, sat_grape_season):
    """
    Щоденне контрольне повідомлення о 12:00.

    yesterday_str    — дата вчорашнього дня (рядок 'YYYY-MM-DD')
    yesterday_stats  — {tmin, tmax, tday, tnight} за вчора
    yesterday_apple  — внесок у САТ яблуні за вчора (°C)
    yesterday_grape  — внесок у САТ винограду за вчора (°C)
    yesterday_precip — опади за вчора (мм)
    period_start_str — дата початку поточного періоду ('YYYY-MM-DD')
    sat_apple_period — накопичена САТ яблуні за період (°C)
    sat_grape_period — накопичена САТ винограду за період (°C)
    sat_apple_season — накопичена САТ яблуні за сезон (°C)
    sat_grape_season — накопичена САТ винограду за сезон (°C)
    """
    # Форматування дат для відображення
    ydate  = date.fromisoformat(yesterday_str)
    pstart = date.fromisoformat(period_start_str)
    today  = date.today()

    ydate_fmt  = ydate.strftime("%d.%m.%Y")
    pstart_fmt = pstart.strftime("%d.%m")
    today_fmt  = (today - timedelta(days=1)).strftime("%d.%m")  # вчора як кінець

    st = yesterday_stats or {}
    left_apple = max(0.0, 2000 - sat_apple_season)
    left_grape = max(0.0, 3000 - sat_grape_season)

    lines = [
        f"Контроль за {ydate_fmt}",
        f"Tmin: {_f(st.get('tmin'))}°C   Tmax: {_f(st.get('tmax'))}°C",
        f"Tніч: {_f(st.get('tnight'))}°C   Tдень: {_f(st.get('tday'))}°C",
        f"Опади: {_f(yesterday_precip)} мм (орієнт.)",
        f"САТ яблуня вчора:   +{_f(yesterday_apple)}°C",
        f"САТ виноград вчора: +{_f(yesterday_grape)}°C",
        f"=Накопичено з {pstart_fmt} по {today_fmt}.{today.strftime('%m')}=",
        f"САТ яблуня:   {_f(sat_apple_period)}°C",
        f"(залишок {left_apple:.0f}°C до 2000)".replace(".", ","),
        f"САТ виноград: {_f(sat_grape_period)}°C",
        f"(залишок {left_grape:.0f}°C до 3000)".replace(".", ","),
    ]
    return "\n".join(lines)


def period_report(period_start_str, period_end_str,
                  period_stats, sat_apple_period, sat_grape_period,
                  precip_period, period_frost_events,
                  season_stats, sat_apple_season, sat_grape_season,
                  precip_season, season_frost_events):
    """
    Підсумковий звіт за 10-денний період (або 3-денний у debug-режимі).

    period_start_str   — початок періоду ('YYYY-MM-DD')
    period_end_str     — кінець періоду ('YYYY-MM-DD')
    period_stats       — {tmin,tmax,tday,tnight} за весь період
    sat_apple_period   — САТ яблуні за період (°C)
    sat_grape_period   — САТ винограду за період (°C)
    precip_period      — опади за період (мм)
    period_frost_events— список {date, tmin} заморозків за період
    season_stats       — {tmin,tmax,tday,tnight} за весь сезон
    sat_apple_season   — САТ яблуні за сезон (°C)
    sat_grape_season   — САТ винограду за сезон (°C)
    precip_season      — опади за сезон (мм)
    season_frost_events— список {date, tmin} заморозків за сезон
    """
    ps = date.fromisoformat(period_start_str)
    pe = date.fromisoformat(period_end_str)
    ps_fmt = ps.strftime("%d.%m.%Y")
    pe_fmt = pe.strftime("%d.%m.%Y")

    left_apple = max(0.0, 2000 - sat_apple_season)
    left_grape = max(0.0, 3000 - sat_grape_season)

    pst = period_stats or {}
    sst = season_stats or {}

    lines = [
        f"Звіт з {ps_fmt} по {pe_fmt}",
        f"Tmin: {_f(pst.get('tmin'))}°C   Tmax: {_f(pst.get('tmax'))}°C",
        f"Tніч: {_f(pst.get('tnight'))}°C   Tдень: {_f(pst.get('tday'))}°C",
        f"САТ яблуня:   {_f(sat_apple_period)}°C",
        f"САТ виноград: {_f(sat_grape_period)}°C",
        f"Опади: {_f(precip_period)} мм (орієнт.)",
        f"Заморозків: {_frost_line(period_frost_events)}",
        "=" * 8 + "За сезон" + "=" * 8,
        f"Tmin: {_f(sst.get('tmin'))}°C   Tmax: {_f(sst.get('tmax'))}°C",
        f"Tніч: {_f(sst.get('tnight'))}°C   Tдень: {_f(sst.get('tday'))}°C",
        f"САТ яблуня:   {_f(sat_apple_season)}°C",
        f"(залишок {left_apple:.0f}°C до 2000)".replace(".", ","),
        f"САТ виноград: {_f(sat_grape_season)}°C",
        f"(залишок {left_grape:.0f}°C до 3000)".replace(".", ","),
        f"Опади: {_f(precip_season)} мм (орієнт.)",
        f"Заморозків: {_frost_line(season_frost_events)}",
    ]
    return "\n".join(lines)


def frost_warning(temp, forecast):
    """
    Негайне попередження про заморозок.
    temp     — поточна температура (°C)
    forecast — {min_temp, min_time} прогноз на 24 год або None
    """
    min_t  = forecast["min_temp"] if forecast else temp
    min_tm = forecast["min_time"][11:16] if forecast else "--:--"
    lines = [
        "УВАГА: ЗАМОРОЗОК",
        f"Зараз:   {_f(temp)}°C",
        f"Прогноз мінімум: {_f(min_t)}°C о {min_tm}",
        "",
        "Яблуня:   небезпека при -2°C (цвітіння)",
        "Виноград: небезпека при -1°C (молоді пагони)",
        "Вживайте захисних заходів!",
    ]
    return "\n".join(lines)