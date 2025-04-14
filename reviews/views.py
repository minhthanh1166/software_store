from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from .models import Review, ReviewResponse
from products.models import Product, OrderItem
from .forms import ReviewForm, ReviewResponseForm
from django.http import JsonResponse

class ReviewListView(ListView):
    model = Review
    template_name = 'reviews/review_list.html'
    context_object_name = 'reviews'
    paginate_by = 10

    def get_queryset(self):
        return Review.objects.filter(is_approved=True)

class ReviewDetailView(DetailView):
    model = Review
    template_name = 'reviews/review_detail.html'
    context_object_name = 'review'

class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/review_form.html'
    
    def get_success_url(self):
        return reverse('products:detail', kwargs={'pk': self.kwargs.get('product_id')})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.kwargs.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        context['product'] = product
        return context
    
    def form_valid(self, form):
        product_id = self.kwargs.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        
        # Check if user has already reviewed this product
        if Review.objects.filter(product=product, user=self.request.user).exists():
            messages.error(self.request, _('You have already reviewed this product'))
            return redirect('products:detail', pk=product_id)
        
        # Check if user has purchased the product
        has_purchased = OrderItem.objects.filter(
            order__user=self.request.user,
            product=product,
            order__status='completed'
        ).exists()
        
        review = form.save(commit=False)
        review.product = product
        review.user = self.request.user
        review.is_verified_purchase = has_purchased
        
        # Automatically approve reviews
        review.is_approved = True
        
        review.save()
        
        messages.success(self.request, _('Review submitted successfully'))
        return super().form_valid(form)

class ReviewUpdateView(LoginRequiredMixin, UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/review_form.html'
    success_url = reverse_lazy('reviews:list')

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

class ReviewDeleteView(LoginRequiredMixin, DeleteView):
    model = Review
    template_name = 'reviews/review_confirm_delete.html'
    success_url = reverse_lazy('reviews:list')

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

class ReviewResponseCreateView(LoginRequiredMixin, CreateView):
    model = ReviewResponse
    form_class = ReviewResponseForm
    template_name = 'reviews/review_response_form.html'
    success_url = reverse_lazy('reviews:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, id=review_id)
        context['review'] = review
        return context

    def form_valid(self, form):
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, id=review_id)
        
        response = form.save(commit=False)
        response.review = review
        response.user = self.request.user
        response.save()
        
        messages.success(self.request, _('Response submitted successfully'))
        return super().form_valid(form)

@login_required
def mark_helpful(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    
    # Toggle helpful status
    if request.user in review.helpful_votes.all():
        review.helpful_votes.remove(request.user)
        user_voted = False
    else:
        review.helpful_votes.add(request.user)
        user_voted = True
    
    # Trả về JSON response nếu là AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'helpful_votes': review.helpful_count,
            'helpful_count': review.helpful_count,
            'user_voted': user_voted
        })
    
    messages.success(request, _('Thank you for your feedback!'))
    # Redirect to product detail page instead of review detail page
    return redirect('products:detail', pk=review.product.id)
