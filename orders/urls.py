from django.urls import path
from . import views
from django.shortcuts import redirect

app_name = 'orders'

urlpatterns = [
    # Order URLs
    path('', views.OrderListView.as_view(), name='list'),
    path('cart/', views.cart, name='cart'),
    path('create/', views.create_order, name='create'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='detail'),
    
    # Cart URLs
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    
    # Payment URLs
    path('payment/checkout/<int:order_id>/', views.payment_checkout, name='payment_checkout'),
    path('payment/notify/', views.payment_notify, name='payment_notify'),
    path('payment/check/<int:order_id>/', views.check_payment_status, name='check_payment_status'),
] 