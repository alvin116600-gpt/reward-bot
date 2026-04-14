from __future__ import annotations


def format_currency(value: object) -> str:
    number = _to_float(value)
    return f'{number:,.0f} đ'


def format_percent(value: object) -> str:
    number = _to_float(value)
    return f'{number *100}%'


def _to_float(value: object) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(',', '')
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0
