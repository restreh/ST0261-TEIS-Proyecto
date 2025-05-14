from decimal import Decimal
from django.conf import settings
from django.core.cache import cache
import requests

def get_exchange_rate(base_currency='USD', target_currency='COP'):
    if base_currency == target_currency:
        return Decimal('1.0')
    
    cache_key = f'exchange_rate_{base_currency}_{target_currency}'
    rate = cache.get(cache_key)
    
    if not rate:
        try:
            response = requests.get(
                f'https://v6.exchangerate-api.com/v6/{settings.EXCHANGE_RATE_API_KEY}/pair/{base_currency}/{target_currency}',
                timeout=5
            )
            data = response.json()
            rate = Decimal(str(data.get('conversion_rate', '1.0')))
            cache.set(cache_key, rate, 86400)  # 24 horas
        except Exception as e:
            print(f"Error obteniendo tasa de cambio: {e}")
            rate = Decimal('1.0')
    
    return rate