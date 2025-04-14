def cart_info(request):
    """
    Context processor để cung cấp thông tin giỏ hàng cho tất cả template
    """
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values())  # Tổng số lượng sản phẩm trong giỏ
    
    return {
        'cart_count': cart_count
    } 