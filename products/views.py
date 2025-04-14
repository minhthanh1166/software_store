from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponse, FileResponse, JsonResponse
from .models import Category, Product, Review, Wishlist
from .forms import ProductForm, ProductScreenshotForm, ProductSearchForm, ReviewForm
from orders.models import Order, OrderItem
import os
from django.conf import settings
import mimetypes
from django.views.decorators.http import require_POST

class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        form = ProductSearchForm(self.request.GET)
        
        if form.is_valid():
            query = form.cleaned_data.get('query')
            category = form.cleaned_data.get('category')
            software_type = form.cleaned_data.get('software_type')
            min_price = form.cleaned_data.get('min_price')
            max_price = form.cleaned_data.get('max_price')

            if query:
                queryset = queryset.filter(
                    Q(name__icontains=query) |
                    Q(description__icontains=query)
                )
            
            if category:
                queryset = queryset.filter(category=category)
            
            if software_type:
                queryset = queryset.filter(software_type=software_type)
            
            if min_price:
                queryset = queryset.filter(price__gte=min_price)
            
            if max_price:
                queryset = queryset.filter(price__lte=max_price)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ProductSearchForm(self.request.GET)
        context['categories'] = Category.objects.all()
        context['featured_products'] = Product.objects.filter(is_featured=True, is_active=True)[:4]
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['screenshots'] = product.screenshots.all()
        context['related_products'] = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]
        
        # Kiểm tra xem sản phẩm đã được thêm vào danh sách yêu thích chưa
        if self.request.user.is_authenticated:
            context['is_favorited'] = Wishlist.objects.filter(
                user=self.request.user,
                product=product
            ).exists()
        
        return context

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:list')

    def form_valid(self, form):
        form.instance.developer = self.request.user
        return super().form_valid(form)

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:list')

    def get_queryset(self):
        return Product.objects.filter(developer=self.request.user)

class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'products/product_confirm_delete.html'
    success_url = reverse_lazy('products:list')

    def get_queryset(self):
        return Product.objects.filter(developer=self.request.user)

@login_required
def add_screenshot(request, product_id):
    product = get_object_or_404(Product, id=product_id, developer=request.user)
    
    if request.method == 'POST':
        form = ProductScreenshotForm(request.POST, request.FILES)
        if form.is_valid():
            screenshot = form.save(commit=False)
            screenshot.product = product
            screenshot.save()
            return redirect('products:detail', pk=product.id)
    else:
        form = ProductScreenshotForm()
    
    return render(request, 'products/add_screenshot.html', {
        'form': form,
        'product': product
    })

class CategoryListView(ListView):
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'

class CategoryDetailView(DetailView):
    model = Category
    template_name = 'products/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        context['products'] = Product.objects.filter(
            category=category,
            is_active=True
        )
        return context

class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'products/review_form.html'

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

@login_required
def download_product(request, product_id, order_id):
    """
    Xử lý tải xuống sản phẩm sau khi thanh toán thành công
    """
    # Kiểm tra đơn hàng tồn tại và thuộc về người dùng hiện tại
    order = get_object_or_404(Order, id=order_id, user=request.user, status='completed')
    
    # Kiểm tra xem sản phẩm có trong đơn hàng không
    order_item = get_object_or_404(OrderItem, order=order, product_id=product_id)
    
    # Lấy thông tin sản phẩm
    product = order_item.product
    
    # Kiểm tra file tồn tại
    if not product.file or not os.path.exists(product.file.path):
        messages.error(request, _('File không tồn tại hoặc đã bị xóa.'))
        return redirect('orders:detail', pk=order_id)
    
    # Tăng số lần tải xuống
    order_item.download_count += 1
    order_item.save()
    
    # Chuẩn bị response để tải file
    file_path = product.file.path
    filename = os.path.basename(file_path)
    
    # Xác định loại mime từ đuôi file
    content_type, encoding = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = 'application/octet-stream'
    
    # Tạo response với file
    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@login_required
@require_POST
def toggle_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if not created:
        wishlist_item.delete()
        is_favorite = False
    else:
        is_favorite = True
        
    return JsonResponse({
        'status': 'success',
        'is_favorite': is_favorite,
        'favorite_count': product.wishlisted_by.count()
    })
