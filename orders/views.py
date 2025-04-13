from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db import transaction
from django.core.cache import cache
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.cache import never_cache
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from .models import Order, OrderItem
from products.models import Product
from .payments import SePay
import uuid
import json
import secrets
from decimal import Decimal
from functools import wraps
from datetime import datetime, timedelta
import traceback
import logging
from django.db import connection
from django.utils import timezone

# Khởi tạo logger
logger = logging.getLogger(__name__)

def rate_limit(key_prefix, limit=60, period=60):
    """
    Decorator giới hạn tốc độ truy cập
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            key = f"ratelimit:{key_prefix}:{request.user.id}"
            count = cache.get(key, 0)
            
            if count >= limit:
                messages.error(request, _('Quá nhiều yêu cầu. Vui lòng thử lại sau.'))
                return redirect('products:list')
            
            cache.set(key, count + 1, period)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

@login_required
@never_cache
def cart(request):
    """
    Hiển thị giỏ hàng
    """
    cart = request.session.get('cart', {})
    cart_items = []
    total_amount = Decimal('0')
    
    if cart:
        products = Product.objects.filter(id__in=cart.keys(), is_active=True)
        for product in products:
            quantity = cart.get(str(product.id), 0)
            total = product.price * Decimal(str(quantity))
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total': total
            })
            total_amount += total
    
    return render(request, 'orders/cart.html', {
        'cart_items': cart_items,
        'total_amount': total_amount
    })

class OrderListView(LoginRequiredMixin, ListView):
    """
    Hiển thị danh sách đơn hàng đã hoàn thành của người dùng
    """
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        cache_key = f'user_completed_orders_{self.request.user.id}'
        queryset = cache.get(cache_key)
        
        if queryset is None:
            queryset = Order.objects.filter(
                user=self.request.user,
                status='completed'
            ).select_related('user').prefetch_related('items', 'items__product').order_by('-created_at')
            cache.set(cache_key, queryset, 300)  # Cache 5 phút
            
        return queryset

class OrderDetailView(LoginRequiredMixin, DetailView):
    """
    Hiển thị chi tiết đơn hàng
    """
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related('user').prefetch_related('items', 'items__product')

    def get_object(self, queryset=None):
        cache_key = f'order_{self.kwargs["pk"]}'
        order = cache.get(cache_key)
        
        if order is None:
            order = super().get_object(queryset)
            cache.set(cache_key, order, 300)  # Cache 5 phút
            
        return order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        
        context['payment_status'] = {
            'pending': {
                'class': 'bg-yellow-100 text-yellow-800',
                'text': 'Chờ thanh toán',
                'show_payment_button': True
            },
            'completed': {
                'class': 'bg-green-100 text-green-800',
                'text': 'Đã thanh toán',
                'show_payment_button': False
            },
            'cancelled': {
                'class': 'bg-red-100 text-red-800',
                'text': 'Đã hủy',
                'show_payment_button': False
            }
        }.get(order.status, {
            'class': 'bg-gray-100 text-gray-800',
            'text': 'Không xác định',
            'show_payment_button': False
        })
        
        # Nếu đơn hàng đang chờ thanh toán, tạo URL thanh toán SePay
        if order.status == 'pending':
            # Kiểm tra cache trước
            cache_key = f'payment_data_{order.id}'
            payment_data = cache.get(cache_key)
            
            # Nếu không có trong cache, tạo mới
            if payment_data is None:
                try:
                    sepay = SePay()
                    payment_data = sepay.create_payment({
                        'order_id': order.id,
                        'amount': float(order.total_amount),
                        'return_url': self.request.build_absolute_uri(reverse('orders:detail', kwargs={'pk': order.id})),
                        'notify_url': self.request.build_absolute_uri(reverse('orders:payment_notify'))
                    })
                    # Lưu vào cache 14 phút
                    cache.set(cache_key, payment_data, 840)
                    # Log thông tin thanh toán để debug
                    logger.info(f"Payment data created for order {order.id}: {payment_data}")
                except Exception as e:
                    logger.error(f"Error creating payment for order {order.id}: {str(e)}")
                    payment_data = {}
            
            # Lưu URL thanh toán vào context
            context['payment_url'] = payment_data.get('payment_url')
            
            # Nếu không có payment_url, tạo URL mặc định
            if not context.get('payment_url'):
                context['payment_url'] = self.request.build_absolute_uri(
                    reverse('orders:payment_checkout', kwargs={'order_id': order.id})
                )
                logger.info(f"Using fallback payment URL for order {order.id}: {context['payment_url']}")
        
        return context

@login_required
@require_http_methods(["POST"])
@rate_limit('add_to_cart')
def add_to_cart(request, product_id):
    """
    Thêm sản phẩm vào giỏ hàng
    """
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        cart = request.session.get('cart', {})
        
        if str(product_id) in cart:
            cart[str(product_id)] += 1
        else:
            cart[str(product_id)] = 1
        
        request.session['cart'] = cart
        request.session.modified = True
        
        messages.success(request, _('Sản phẩm đã được thêm vào giỏ hàng'))
    except Exception as e:
        messages.error(request, _('Không thể thêm sản phẩm vào giỏ hàng'))
        
    return redirect('products:detail', pk=product_id)

@login_required
@require_http_methods(["POST"])
@rate_limit('remove_from_cart')
def remove_from_cart(request, product_id):
    """
    Xóa sản phẩm khỏi giỏ hàng
    """
    try:
        cart = request.session.get('cart', {})
        
        if str(product_id) in cart:
            del cart[str(product_id)]
            request.session['cart'] = cart
            request.session.modified = True
            messages.success(request, _('Đã xóa sản phẩm khỏi giỏ hàng'))
    except Exception as e:
        messages.error(request, _('Không thể xóa sản phẩm khỏi giỏ hàng'))
    
    return redirect('orders:cart')

@login_required
@require_http_methods(["POST"])
@rate_limit('update_cart')
def update_cart(request, product_id):
    """
    Cập nhật số lượng sản phẩm trong giỏ hàng
    """
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart = request.session.get('cart', {})
            cart[str(product_id)] = min(quantity, 10)  # Giới hạn số lượng tối đa
            request.session['cart'] = cart
            request.session.modified = True
            messages.success(request, _('Đã cập nhật giỏ hàng'))
        else:
            return remove_from_cart(request, product_id)
    except ValueError:
        messages.error(request, _('Số lượng không hợp lệ'))
    except Exception as e:
        messages.error(request, _('Không thể cập nhật giỏ hàng'))
    
    return redirect('orders:cart')

@login_required
@never_cache
@transaction.atomic
@rate_limit('create_order')
def create_order(request):
    """
    Tạo đơn hàng mới từ giỏ hàng và chuyển hướng đến trang thanh toán SePay
    """
    logger = logging.getLogger(__name__)
    
    # Kiểm tra giỏ hàng
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, _('Giỏ hàng của bạn đang trống'))
        return redirect('products:list')

    try:
        # Kiểm tra và lấy thông tin sản phẩm
        product_ids = [int(id) for id in cart.keys()]
        products = Product.objects.filter(id__in=product_ids, is_active=True)
        
        # Đảm bảo tất cả sản phẩm đều có sẵn
        if len(products) != len(cart):
            messages.error(request, _('Một số sản phẩm không còn khả dụng'))
            return redirect('orders:cart')

        # Tính tổng tiền
        total_amount = sum(
            product.price * Decimal(str(cart[str(product.id)]))
            for product in products
        )

        if request.method == 'POST':
            try:
                # Tạo đơn hàng mới
                temp_transaction_id = f"TEMP-{uuid.uuid4().hex}"
                
                # Tạo đơn hàng với đầy đủ thông tin
                order = Order(
                    user=request.user,
                    status='pending',
                    payment_status='pending',
                    total_amount=total_amount,
                    payment_method='sepay',
                    transaction_id=temp_transaction_id,
                    shipping_address=getattr(request.user, 'address', '') or '',
                    shipping_phone=getattr(request.user, 'phone_number', '') or '',
                    shipping_email=request.user.email
                )
                order.save()
                logger.info(f"Đã tạo đơn hàng với ID: {order.id}")
                
                # Tạo chi tiết đơn hàng
                for product in products:
                    quantity = int(cart[str(product.id)])
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price=product.price
                    )
                
                logger.info(f"Đã tạo {len(products)} mục đơn hàng")
                
                # Xóa giỏ hàng sau khi tạo đơn hàng thành công
                del request.session['cart']
                request.session.modified = True
                
                # Khởi tạo cổng thanh toán SePay
                sepay = SePay()
                
                # Tạo thông tin thanh toán
                payment_data = sepay.create_payment({
                    'order_id': order.id,
                    'amount': float(order.total_amount),
                    'return_url': request.build_absolute_uri(reverse('orders:detail', kwargs={'pk': order.id})),
                    'notify_url': request.build_absolute_uri(reverse('orders:payment_notify'))
                })
                
                # Lưu thông tin thanh toán vào cache
                cache_key = f'payment_data_{order.id}'
                cache.set(cache_key, payment_data, 840)  # Lưu trong 14 phút
                
                # Chuyển hướng trực tiếp đến trang thanh toán SePay
                if 'payment_url' in payment_data:
                    return redirect(payment_data['payment_url'])
                else:
                    # Nếu không có URL thanh toán, chuyển về trang checkout
                    return redirect('orders:payment_checkout', order_id=order.id)
                
            except Exception as e:
                logger.error(f"Lỗi khi tạo đơn hàng: {str(e)}")
                logger.error(f"Loại lỗi: {type(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                messages.error(request, _('Không thể tạo đơn hàng. Vui lòng thử lại sau.'))
                return redirect('orders:cart')

        # Hiển thị giỏ hàng nếu không phải POST request
        context = {
            'cart_items': [
                {
                    'product': product,
                    'quantity': cart[str(product.id)],
                    'total': product.price * Decimal(str(cart[str(product.id)]))
                }
                for product in products
            ],
            'total_amount': total_amount
        }
        
        return render(request, 'orders/cart.html', context)
    
    except Exception as e:
        logger.error(f"Lỗi trong create_order: {str(e)}")
        logger.error(f"Loại lỗi: {type(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        messages.error(request, _('Đã xảy ra lỗi. Vui lòng thử lại sau.'))
        return redirect('orders:cart')

@login_required
@rate_limit('payment_checkout')
def payment_checkout(request, order_id):
    try:
        order = Order.objects.select_related('user').get(id=order_id, user=request.user)
        
        # Nếu đơn hàng đã hoàn thành, chuyển hướng đến trang chi tiết đơn hàng
        if order.status == 'completed':
            messages.info(request, 'Đơn hàng này đã được thanh toán.')
            return redirect('orders:order_detail', pk=order.id)
            
        # Khởi tạo cổng thanh toán SePay
        sepay = SePay()
        
        # Tạo cache key cho thanh toán
        cache_key = f'payment_data_{order.id}'
        payment_data = cache.get(cache_key)
        
        # Nếu không có dữ liệu thanh toán trong cache hoặc request có tham số refresh
        if payment_data is None or request.GET.get('refresh'):
            payment_data = sepay.create_payment({
                'order_id': order.id,
                'amount': float(order.total_amount),
                'return_url': request.build_absolute_uri(reverse('orders:order_detail', kwargs={'pk': order.id})),
                'notify_url': request.build_absolute_uri(reverse('orders:payment_notify'))
            })
            # Lưu vào cache trong 14 phút (900 - 60 giây)
            cache.set(cache_key, payment_data, 840)
        
        context = {
            'order': order,
            'payment_data': payment_data,
        }
        return render(request, 'orders/checkout.html', context)
    except Order.DoesNotExist:
        messages.error(request, 'Không tìm thấy đơn hàng.')
        return redirect('orders:list')
    except Exception as e:
        logger.error(f"Payment checkout error for order {order_id}: {str(e)}")
        messages.error(request, 'Có lỗi xảy ra khi xử lý thanh toán. Vui lòng thử lại sau.')
        return redirect('orders:list')

@csrf_exempt
@require_POST
def payment_notify(request):
    """
    Xử lý thông báo thanh toán từ cổng thanh toán SePay
    Endpoint này sẽ được gọi bởi cổng thanh toán khi có kết quả thanh toán
    """
    try:
        # Lấy dữ liệu từ POST request
        payment_data = json.loads(request.body)
        
        # Khởi tạo cổng thanh toán SePay
        sepay = SePay()
        
        # Xác minh tính hợp lệ của thông báo thanh toán
        verification = sepay.verify_payment(payment_data)
        
        if verification.get('success'):
            # Lấy thông tin đơn hàng
            order_id = verification.get('order_id')
            transaction_id = verification.get('transaction_id')
            
            # Cập nhật trạng thái đơn hàng
            try:
                with transaction.atomic():
                    order = Order.objects.select_for_update().get(id=order_id)
                    
                    # Chỉ cập nhật nếu đơn hàng chưa hoàn thành
                    if order.status != 'completed':
                        order.status = 'completed'
                        order.transaction_id = transaction_id
                        order.save()
                        
                        # Tạo license key và download URL cho từng mục đơn hàng
                        for item in order.orderitem_set.all():
                            # Kiểm tra xem item đã có license_key chưa
                            if not item.license_key:
                                item.license_key = f"SW-{order.id}-{item.product.id}-{secrets.token_hex(8).upper()}"
                                item.download_url = reverse('products:download', kwargs={'product_id': item.product.id, 'order_id': order.id})
                                item.save()
                        
                        # Xóa cache thanh toán
                        cache.delete(f'payment_data_{order.id}')
                        
                        # Gửi email thông báo
                        # send_order_confirmation.delay(order.id)
                
                return JsonResponse({'status': 'success'})
            except Order.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)
            except Exception as e:
                logger.error(f"Error updating order {order_id}: {str(e)}")
                return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)
        else:
            # Ghi log lỗi nếu xác minh thất bại
            logger.warning(f"Invalid payment notification: {payment_data}")
            return JsonResponse({'status': 'error', 'message': 'Invalid payment data'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Payment notification error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)

@login_required
def check_payment_status(request, order_id):
    """
    Kiểm tra trạng thái thanh toán của đơn hàng
    Endpoint này được gọi qua AJAX từ trang thanh toán
    """
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        
        # Nếu đơn hàng đã hoàn thành, trả về trạng thái completed
        if order.status == 'completed':
            return JsonResponse({
                'status': 'completed',
                'redirect_url': reverse('orders:order_detail', kwargs={'pk': order.id})
            })
        
        # Nếu đơn hàng bị hủy, trả về trạng thái cancelled
        if order.status == 'cancelled':
            return JsonResponse({
                'status': 'cancelled',
                'message': 'Đơn hàng đã bị hủy.'
            })
        
        # Kiểm tra trạng thái từ cổng thanh toán nếu có transaction_id
        if order.transaction_id:
            sepay = SePay()
            result = sepay.query_transaction(order.transaction_id)
            
            if result.get('success') and result.get('status') == 'paid':
                # Cập nhật trạng thái đơn hàng nếu thanh toán thành công
                with transaction.atomic():
                    order.status = 'completed'
                    order.save()
                    
                    # Tạo license key và download URL cho từng mục đơn hàng
                    for item in order.orderitem_set.all():
                        if not item.license_key:
                            item.license_key = f"SW-{order.id}-{item.product.id}-{secrets.token_hex(8).upper()}"
                            item.download_url = reverse('products:download', kwargs={'product_id': item.product.id, 'order_id': order.id})
                            item.save()
                
                # Gửi email thông báo
                # send_order_confirmation.delay(order.id)
                
                return JsonResponse({
                    'status': 'completed',
                    'redirect_url': reverse('orders:order_detail', kwargs={'pk': order.id})
                })
        
        # Trả về pending nếu chưa hoàn thành hoặc hủy
        return JsonResponse({'status': 'pending'})
    except Order.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Không tìm thấy đơn hàng'}, status=404)
    except Exception as e:
        logger.error(f"Check payment status error for order {order_id}: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Lỗi hệ thống'}, status=500)
