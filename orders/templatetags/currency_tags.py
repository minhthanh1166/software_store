from django import template
from django.template.defaultfilters import floatformat
from django.conf import settings
from django.utils.translation import get_language
from decimal import Decimal

register = template.Library()

@register.filter(name='currency')
def currency(value):
    """
    Format a number as Vietnamese currency (VND)
    """
    try:
        # Always use VND settings
        currency_settings = {
            'code': 'VND',
            'symbol': '₫',
            'position': 'after',
            'decimal_places': 0,
            'thousands_sep': '.',
            'decimal_sep': ',',
        }
        
        # Convert value to Decimal if not already
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
            
        # Round to 0 decimal places
        value = round(value, 0)
        
        # Format the number with thousand separators
        number_parts = str(value).split('.')
        integer_part = number_parts[0]
        
        # Add thousand separators
        if len(integer_part) > 3:
            formatted_integer = ''
            for i, digit in enumerate(reversed(integer_part)):
                if i > 0 and i % 3 == 0:
                    formatted_integer = '.' + formatted_integer
                formatted_integer = digit + formatted_integer
        else:
            formatted_integer = integer_part
            
        # Always position symbol after the number
        return f"{formatted_integer}{currency_settings['symbol']}"
            
    except (ValueError, TypeError):
        return value 