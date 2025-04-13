from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment URLs
    path('', views.PaymentListView.as_view(), name='list'),
    path('<int:pk>/', views.PaymentDetailView.as_view(), name='detail'),
    path('order/<int:order_id>/', views.PaymentCreateView.as_view(), name='create'),
    
    # Refund URLs
    path('refund/<int:payment_id>/', views.RefundCreateView.as_view(), name='create_refund'),
    path('refund/process/<int:refund_id>/', views.process_refund, name='process_refund'),

    path('checkout/<int:order_id>/', views.checkout, name='checkout'),
    path('notify/', views.payment_notify, name='payment_notify'),
    path('return/', views.payment_return, name='payment_return'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),
    path('refund/<int:order_id>/', views.refund_request, name='refund_request'),
] 