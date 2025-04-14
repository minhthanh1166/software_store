from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Lấy giá trị từ dictionary theo key.
    Sử dụng: {{ dictionary|get_item:key }}
    """
    key = str(key)  # Đảm bảo key là string
    if key.isdigit():  # If the key is a digit, try it as an integer
        try:
            return dictionary.get(int(key), 0)
        except (ValueError, KeyError):
            pass
    return dictionary.get(key, 0)

@register.filter
def multiply(value, arg):
    """
    Nhân value với arg.
    Sử dụng: {{ value|multiply:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0 