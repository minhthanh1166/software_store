from django import template
from django.conf import settings
from django.utils.translation import get_language
from decimal import Decimal

register = template.Library()

@register.filter(name='currency')
def currency(value):
    try:
        # Lấy ngôn ngữ hiện tại
        current_language = get_language() or settings.LANGUAGE_CODE
        
        # Lấy cấu hình tiền tệ cho ngôn ngữ hiện tại
        currency_settings = settings.CURRENCY_LOCALE.get(current_language, settings.CURRENCY_LOCALE['en'])
        
        # Chuyển đổi giá trị sang Decimal nếu chưa phải
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
            
        # Làm tròn số theo số thập phân được cấu hình
        value = round(value, currency_settings['decimal_places'])
        
        # Định dạng số
        number_parts = str(value).split('.')
        integer_part = number_parts[0]
        
        # Thêm dấu phân cách hàng nghìn
        if len(integer_part) > 3:
            formatted_integer = ''
            for i, digit in enumerate(reversed(integer_part)):
                if i > 0 and i % 3 == 0:
                    formatted_integer = currency_settings['thousands_sep'] + formatted_integer
                formatted_integer = digit + formatted_integer
        else:
            formatted_integer = integer_part
            
        # Xử lý phần thập phân
        if currency_settings['decimal_places'] > 0 and len(number_parts) > 1:
            decimal_part = number_parts[1].ljust(currency_settings['decimal_places'], '0')
            formatted_number = f"{formatted_integer}{currency_settings['decimal_sep']}{decimal_part}"
        else:
            formatted_number = formatted_integer
            
        # Thêm ký hiệu tiền tệ theo vị trí
        if currency_settings['position'] == 'before':
            return f"{currency_settings['symbol']}{formatted_number}"
        else:
            return f"{formatted_number}{currency_settings['symbol']}"
            
    except (ValueError, TypeError):
        return value
        
@register.filter(name='currency_code')
def currency_code(value):
    current_language = get_language() or settings.LANGUAGE_CODE
    currency_settings = settings.CURRENCY_LOCALE.get(current_language, settings.CURRENCY_LOCALE['en'])
    return currency_settings['code'] 

@register.filter(name='multiply')
def multiply(value, arg):
    """
    Nhân value với arg
    """
    try:
        if isinstance(value, str):
            value = float(value.replace(',', '.'))
        if isinstance(arg, str):
            arg = float(arg.replace(',', '.'))
        return value * arg
    except (ValueError, TypeError):
        return 0 