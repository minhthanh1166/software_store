from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from .models import Review, ReviewResponse
from products.models import Product
from .forms import ReviewForm, ReviewResponseForm

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.kwargs.get('product_id')
        context['product'] = get_object_or_404(Product, id=product_id)
        return context

    def form_valid(self, form):
        product_id = self.kwargs.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        
        # Kiểm tra xem người dùng đã đánh giá sản phẩm này chưa
        if Review.objects.filter(product=product, user=self.request.user).exists():
            messages.error(self.request, 'Bạn đã đánh giá sản phẩm này rồi')
            return self.form_invalid(form)
        
        # Kiểm tra xem người dùng đã mua sản phẩm chưa
        has_purchased = product.order_items.filter(
            order__user=self.request.user,
            order__payment_status=True
        ).exists()
        
        review = form.save(commit=False)
        review.product = product
        review.user = self.request.user
        review.is_verified_purchase = has_purchased
        review.save()
        
        messages.success(self.request, 'Cảm ơn bạn đã đánh giá sản phẩm!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('products:detail', kwargs={'pk': self.object.product.id})

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
    
    if request.user not in review.helpful_votes.all():
        review.helpful_votes.add(request.user)
        review.helpful_count = review.helpful_votes.count()
        review.save()
        messages.success(request, _('Review marked as helpful'))
    else:
        review.helpful_votes.remove(request.user)
        review.helpful_count = review.helpful_votes.count()
        review.save()
        messages.success(request, _('Helpful vote removed'))
    
    return redirect('reviews:detail', pk=review.id)
