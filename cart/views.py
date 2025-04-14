from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from .models import Cart, CartItem
from products.models import Product
from django.http import JsonResponse


@login_required
def cart_detail(request):
    """
    Display the user's cart
    """
    cart, created = Cart.objects.prefetch_related('items__product').get_or_create(user=request.user)
    
    return render(request, 'cart/cart_detail.html', {
        'cart': cart,
        'cart_items': cart.items.all(),
    })


@login_required
@require_POST
def add_to_cart(request, product_id):
    """
    Add a product to the user's cart
    Each product can only be added once (quantity always 1)
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Check if product already exists in cart
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )
    
    if not item_created:
        # Product already in cart - no need to update quantity as it's always 1
        messages.info(request, _('Product already in cart'))
    else:
        messages.success(request, _('Product added to cart'))
    
    cart.save()  # Update the cart timestamp
    
    # For AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': _('Product added to cart'),
            'cart_count': cart.count,
            'cart_total': cart.total,
        })
    
    next_url = request.POST.get('next', 'cart:cart_detail')
    return redirect(next_url)


@login_required
@require_POST
def remove_from_cart(request, item_id):
    """
    Remove an item from the user's cart
    """
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    
    messages.success(request, _('Product removed from cart'))
    
    # For AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart = cart_item.cart
        return JsonResponse({
            'success': True,
            'message': _('Product removed from cart'),
            'cart_count': cart.count,
            'cart_total': cart.total,
        })
    
    return redirect('cart:cart_detail')


@login_required
@require_POST
def clear_cart(request):
    """
    Remove all items from the user's cart
    """
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart.items.all().delete()
    
    messages.success(request, _('Cart cleared'))
    
    # For AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': _('Cart cleared'),
            'cart_count': 0,
            'cart_total': 0,
        })
    
    return redirect('cart:cart_detail') 