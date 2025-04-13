from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter(name='currency')
def currency(value):
    """
    Format a number as Vietnamese currency (VND)
    Example: 1000000 -> 1.000.000 VNĐ
    """
    if value is None:
        return '0 VNĐ'
    
    # Format with floatformat to remove decimal places
    formatted = floatformat(value, 0)
    
    # Add thousand separators (. in Vietnamese format)
    parts = []
    while formatted:
        parts.append(formatted[-3:])
        formatted = formatted[:-3]
    
    formatted = '.'.join(reversed(parts))
    
    # Return with VND currency symbol
    return f"{formatted} VNĐ" 