# ============================================================
# calculator.py | CAT_0626_bot
# Розрахунок САТ і температурних показників
# Tmin, Tmax, Tніч (00:00-06:00 + 22:00-24:00), Tдень (06:00-22:00)
# ============================================================

from config import BASE_APPLE, BASE_GRAPE, HOUR_FRACTION, DAY_START, DAY_END


def apple_contribution(temperature):
    """
    Внесок у САТ яблуні за 2 год (поріг BASE_APPLE = +5°C).
    Повертає 0 якщо температура нижча або рівна порогу.
    """
    if temperature is None:
        return 0.0
    diff = temperature - BASE_APPLE
    return round(diff * HOUR_FRACTION, 4) if diff > 0 else 0.0


def grape_contribution(temperature):
    """
    Внесок у САТ винограду за 2 год (поріг BASE_GRAPE = +10°C).
    Повертає 0 якщо температура нижча або рівна порогу.
    """
    if temperature is None:
        return 0.0
    diff = temperature - BASE_GRAPE
    return round(diff * HOUR_FRACTION, 4) if diff > 0 else 0.0


def calc_temp_stats(hourly_temps):
    """
    Розрахунок температурних показників з масиву 24 погодинних значень.
    hourly_temps — список з 24 температур (індекс 0 = 00:00 ... 23 = 23:00)

    Нічні години: 00:00–05:00 і 22:00–23:00 (DAY_START=6, DAY_END=22)
    Денні години: 06:00–21:00

    Повертає словник {tmin, tmax, tday, tnight} або None при помилці.
    tmin   — абсолютний мінімум за добу (°C)
    tmax   — абсолютний максимум за добу (°C)
    tday   — середня денна температура (°C)
    tnight — середня нічна температура (°C)
    """
    if not hourly_temps:
        return None

    night_hours = list(range(0, DAY_START)) + list(range(DAY_END, 24))
    night_temps = [hourly_temps[h] for h in night_hours
                   if h < len(hourly_temps) and hourly_temps[h] is not None]
    day_temps   = [hourly_temps[h] for h in range(DAY_START, DAY_END)
                   if h < len(hourly_temps) and hourly_temps[h] is not None]
    all_valid   = [t for t in hourly_temps if t is not None]

    if not all_valid:
        return None

    return {
        "tmin":   round(min(all_valid), 1),
        "tmax":   round(max(all_valid), 1),
        "tday":   round(sum(day_temps)   / len(day_temps),   1) if day_temps   else None,
        "tnight": round(sum(night_temps) / len(night_temps), 1) if night_temps else None,
    }


def merge_temp_stats(stats_list):
    """
    Об'єднання температурних показників за кілька днів в підсумок за період.
    stats_list — список словників {tmin, tmax, tday, tnight} за кожен день.

    tmin/tmax   — абсолютні екстремуми за весь період
    tday/tnight — середні за весь період (середнє денних/нічних середніх)
    """
    valid = [s for s in stats_list if s]
    if not valid:
        return None
    tmins   = [s["tmin"]   for s in valid if s.get("tmin")   is not None]
    tmaxs   = [s["tmax"]   for s in valid if s.get("tmax")   is not None]
    tdays   = [s["tday"]   for s in valid if s.get("tday")   is not None]
    tnights = [s["tnight"] for s in valid if s.get("tnight") is not None]
    return {
        "tmin":   min(tmins)                               if tmins   else None,
        "tmax":   max(tmaxs)                               if tmaxs   else None,
        "tday":   round(sum(tdays)   / len(tdays),   1)   if tdays   else None,
        "tnight": round(sum(tnights) / len(tnights), 1)   if tnights else None,
    }