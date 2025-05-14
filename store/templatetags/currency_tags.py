# store/templatetags/currency_tags.py
from django import template
from django.conf import settings

register = template.Library()

@register.filter
def currency_symbol(currency_code):
    symbols = {
        'USD': '$',
        'COP': '$',
        'EUR': '€'
    }
    return symbols.get(currency_code, '$')

@register.filter(name='multiply')
def multiply(value, arg):
    """Filtro para multiplicar valores en templates"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0