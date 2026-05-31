# ============================================================
# calculator.py | CAT_bot
# Розрахунок внеску температури в суму активних температур (САТ)
# ============================================================

from config import BASE_APPLE, BASE_GRAPE, HOUR_FRACTION


def sat_contribution(temperature, base):
    """
    Функція обчислення активного внеску однієї температурної точки.
    Якщо температура вища за поріг — повертає різницю × частку доби.
    Якщо нижча або рівна — повертає 0.
    temperature — поточна температура (°C)
    base        — поріг активної температури (°C)
    """
    if temperature is None:
        return 0.0
    diff = temperature - base
    return round(diff * HOUR_FRACTION, 4) if diff > 0 else 0.0


def apple_contribution(temperature):
    """Внесок у САТ яблуні (поріг BASE_APPLE = +5°C)"""
    return sat_contribution(temperature, BASE_APPLE)


def grape_contribution(temperature):
    """Внесок у САТ винограду (поріг BASE_GRAPE = +10°C)"""
    return sat_contribution(temperature, BASE_GRAPE)