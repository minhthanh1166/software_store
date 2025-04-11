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
] 