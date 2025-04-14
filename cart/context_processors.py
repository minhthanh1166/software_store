from .models import Cart

def cart_processor(request):
    """
    Context processor that adds cart information to all templates
    """
    cart_count = 0
    cart_total = 0
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.filter(user=request.user).first()
            if cart:
                cart_count = cart.count
                cart_total = cart.total
        except Exception:
            # Handle any errors silently
            pass
            
    return {
        'cart_count': cart_count,
        'cart_total': cart_total
    } 