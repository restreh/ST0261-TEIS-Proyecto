from django.conf import settings
from .currency import get_exchange_rate

def currency_context(request):
    selected_currency = request.session.get('currency', 'USD')
    if selected_currency not in settings.CURRENCIES:
        selected_currency = 'USD'
    
    return {
        'selected_currency': selected_currency,
        'exchange_rate': get_exchange_rate('USD', selected_currency),
        'currency_symbol': '€' if selected_currency == 'EUR' else '$',
        'CURRENCIES': settings.CURRENCIES
    }