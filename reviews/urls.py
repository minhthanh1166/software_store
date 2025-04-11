from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    # Review URLs
    path('', views.ReviewListView.as_view(), name='list'),
    path('<int:pk>/', views.ReviewDetailView.as_view(), name='detail'),
    path('product/<int:product_id>/', views.ReviewCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.ReviewUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='delete'),
    
    # Review Response URLs
    path('<int:review_id>/response/', views.ReviewResponseCreateView.as_view(), name='create_response'),
    
    # Helpful Votes
    path('<int:review_id>/helpful/', views.mark_helpful, name='mark_helpful'),
] 