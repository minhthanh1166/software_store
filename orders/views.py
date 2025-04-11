from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db import transaction
from .models import Order, OrderItem
from products.models import Product
from .forms import OrderForm

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'orders/order_form.html'
    success_url = reverse_lazy('orders:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.request.session.get('cart', {})
        products = Product.objects.filter(id__in=cart.keys())
        context['cart_items'] = [
            {
                'product': product,
                'quantity': cart[str(product.id)],
                'total': product.price * cart[str(product.id)]
            }
            for product in products
        ]
        context['total_amount'] = sum(item['total'] for item in context['cart_items'])
        return context

    @transaction.atomic
    def form_valid(self, form):
        cart = self.request.session.get('cart', {})
        if not cart:
            messages.error(self.request, _('Your cart is empty'))
            return redirect('products:list')

        order = form.save(commit=False)
        order.user = self.request.user
        order.total_amount = sum(
            Product.objects.get(id=product_id).price * quantity
            for product_id, quantity in cart.items()
        )
        order.save()

        # Create order items
        for product_id, quantity in cart.items():
            product = Product.objects.get(id=product_id)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )

        # Clear the cart
        del self.request.session['cart']
        self.request.session.modified = True

        messages.success(self.request, _('Order created successfully'))
        return super().form_valid(form)

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = request.session.get('cart', {})
    
    if str(product_id) in cart:
        cart[str(product_id)] += 1
    else:
        cart[str(product_id)] = 1
    
    request.session['cart'] = cart
    request.session.modified = True
    
    messages.success(request, _('Product added to cart'))
    return redirect('products:detail', pk=product_id)

@login_required
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, _('Product removed from cart'))
    
    return redirect('orders:create')

@login_required
def update_cart(request, product_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart = request.session.get('cart', {})
            cart[str(product_id)] = quantity
            request.session['cart'] = cart
            request.session.modified = True
            messages.success(request, _('Cart updated'))
        else:
            return remove_from_cart(request, product_id)
    
    return redirect('orders:create')
