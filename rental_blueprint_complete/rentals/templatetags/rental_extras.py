from django import template
from django.conf import settings

register = template.Library()


@register.filter
def money(value):
    """25000 -> $25,000. Change the symbol with CURRENCY_SYMBOL in settings.py (default "$")."""
    if value in (None, ""):
        return ""
    symbol = getattr(settings, "CURRENCY_SYMBOL", "$")
    return f"{symbol}{int(round(float(value))):,}"


@register.filter
def stars(value):
    """4.3 -> [True, True, True, True, False] (used to draw filled/empty stars)."""
    rounded = round(float(value or 0))
    return [i < rounded for i in range(5)]
