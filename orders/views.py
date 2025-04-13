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
from cart.models import Cart, CartItem
from payments.sepay import SePay
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
    Hiển thị trang thanh toán với thông tin từ giỏ hàng
    """
    # Lấy giỏ hàng từ database thay vì session
    cart, created = Cart.objects.prefetch_related('items__product').get_or_create(user=request.user)
    cart_items = cart.items.all()
    
    if not cart_items:
        messages.error(request, _('Giỏ hàng của bạn đang trống'))
        return redirect('products:list')
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'payment_methods': [
            {'value': 'sepay', 'name': 'SePay (Thẻ tín dụng, Ví điện tử)'},
            {'value': 'bank', 'name': 'Chuyển khoản ngân hàng'},
        ]
    }
    
    return render(request, 'orders/cart.html', context)

class OrderListView(LoginRequiredMixin, ListView):
    """
    Hiển thị danh sách đơn hàng của người dùng
    """
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        cache_key = f'user_orders_{self.request.user.id}'
        queryset = cache.get(cache_key)
        
        if queryset is None:
            queryset = Order.objects.filter(
                user=self.request.user
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

        # Payment status mapping with improved styling
        payment_statuses = {
            'pending': {
                'class': 'bg-yellow-100 text-yellow-800',
                'text': _('Chờ thanh toán'),
                'show_payment_button': True
            },
            'processing': {
                'class': 'bg-blue-100 text-blue-800',
                'text': _('Đang xử lý'),
                'show_payment_button': False
            },
            'completed': {
                'class': 'bg-green-100 text-green-800',
                'text': _('Đã thanh toán'),
                'show_payment_button': False
            },
            'cancelled': {
                'class': 'bg-red-100 text-red-800',
                'text': _('Đã hủy'),
                'show_payment_button': False
            },
            'failed': {
                'class': 'bg-red-100 text-red-800',
                'text': _('Thất bại'),
                'show_payment_button': True
            }
        }
        
        context['payment_status'] = payment_statuses.get(order.status, {
            'class': 'bg-gray-100 text-gray-800',
            'text': _('Không xác định'),
            'show_payment_button': False
        })
        
        # Nếu đơn hàng đang chờ thanh toán và phương thức là SePay, tạo URL thanh toán
        if order.status == 'pending' and order.payment_method == 'sepay':
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
        
        # Thêm thông tin tài khoản ngân hàng nếu thanh toán qua chuyển khoản
        if order.payment_method == 'bank':
            context['bank_info'] = {
                'bank_name': '',
                'account_number': '',
                'account_holder': '',
                'transfer_content': f'THANHTOAN {order.id}'
            }
        
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
    Tạo đơn hàng mới từ giỏ hàng model và chuyển hướng đến trang thanh toán
    """
    logger = logging.getLogger(__name__)
    
    # Lấy giỏ hàng từ database thay vì session
    cart, created = Cart.objects.prefetch_related('items__product').get_or_create(user=request.user)
    cart_items = cart.items.all()
    
    if not cart_items:
        messages.error(request, _('Giỏ hàng của bạn đang trống'))
        return redirect('products:list')

    try:
        # Danh sách sản phẩm
        products = [item.product for item in cart_items]
        
        # Tổng tiền
        total_amount = cart.total

        if request.method == 'POST':
            try:
                # Lấy phương thức thanh toán từ form
                payment_method = request.POST.get('payment_method', 'sepay')
                
                # Tạo đơn hàng mới
                temp_transaction_id = f"TEMP-{uuid.uuid4().hex}"
                
                # Tạo đơn hàng với đầy đủ thông tin
                order = Order(
                    user=request.user,
                    status='pending',
                    payment_status='pending',
                    total_amount=total_amount,
                    payment_method=payment_method,
                    transaction_id=temp_transaction_id,
                    shipping_address=getattr(request.user, 'address', '') or '',
                    shipping_phone=getattr(request.user, 'phone_number', '') or '',
                    shipping_email=request.user.email
                )
                order.save()
                logger.info(f"Đã tạo đơn hàng với ID: {order.id}")
                
                # Tạo chi tiết đơn hàng - mỗi sản phẩm có số lượng 1
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=1,  # Quantity is always 1
                        price=item.product.price
                    )
                
                logger.info(f"Đã tạo {cart_items.count()} mục đơn hàng")
                
                # Xóa giỏ hàng sau khi tạo đơn hàng thành công
                cart.items.all().delete()
                
                # Xử lý thanh toán theo phương thức đã chọn
                if payment_method == 'sepay':
                    # Chuyển hướng trực tiếp đến trang checkout thay vì trang thanh toán SePay
                    logger.info(f"Chuyển hướng đến trang checkout cho đơn hàng {order.id}")
                    return redirect('orders:payment_checkout', order_id=order.id)
                else:
                    # Chuyển khoản ngân hàng - hiển thị thông tin thanh toán
                    messages.success(request, _('Đơn hàng đã được tạo. Vui lòng hoàn tất thanh toán chuyển khoản.'))
                    return redirect('orders:detail', pk=order.id)
                
            except Exception as e:
                logger.error(f"Lỗi khi tạo đơn hàng: {str(e)}")
                logger.error(f"Loại lỗi: {type(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                messages.error(request, _('Không thể tạo đơn hàng. Vui lòng thử lại sau.'))
                return redirect('orders:cart')

        # Hiển thị trang checkout nếu không phải POST request
        return redirect('orders:cart')
    
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
            messages.info(request, _('Đơn hàng này đã được thanh toán.'))
            return redirect('orders:detail', pk=order.id)
            
        # Khởi tạo cổng thanh toán SePay
        sepay = SePay()
        
        # Tạo UUID cho giao dịch này để tránh trùng lặp
        transaction_uid = uuid.uuid4().hex[:10].upper()
        
        # Tạo nội dung chuyển khoản duy nhất với UUID
        transfer_content = f"DH{order.id}-{transaction_uid}"
        
        # Lưu transaction_uid vào order để sau này có thể xác minh
        order.transaction_reference = transaction_uid
        order.save()
        
        # Tạo thông tin thanh toán mới
        payment_data = sepay.create_payment({
            'order_id': order.id,
            'amount': float(order.total_amount),
            'return_url': request.build_absolute_uri(reverse('orders:detail', kwargs={'pk': order.id})),
            'notify_url': request.build_absolute_uri(reverse('orders:payment_notify')),
            'transfer_content': transfer_content
        })
        
        # Lưu vào cache trong 15 phút
        cache_key = f'payment_data_{order.id}'
        cache.set(cache_key, payment_data, 900)
        
        logger.info(f"Tạo thông tin thanh toán cho đơn hàng {order.id} với mã giao dịch: {transaction_uid}")
        
        context = {
            'order': order,
            'payment_data': payment_data,
            'bank_info': {
                'bank_name': payment_data.get('bank_name', 'BIDV'),
                'account_number': payment_data.get('account_number', '96247TT123'),
                'account_holder': payment_data.get('account_holder', 'NGUYEN DUY'),
                'transfer_content': payment_data.get('transfer_content', transfer_content)
            }
        }
        return render(request, 'orders/checkout.html', context)
    except Order.DoesNotExist:
        messages.error(request, _('Không tìm thấy đơn hàng.'))
        return redirect('orders:list')
    except Exception as e:
        logger.error(f"Lỗi xử lý thanh toán cho đơn hàng {order_id}: {str(e)}")
        messages.error(request, _('Có lỗi xảy ra khi xử lý thanh toán. Vui lòng thử lại sau.'))
        return redirect('orders:list')

@csrf_exempt
@require_POST
def payment_notify(request):
    """
    Xử lý thông báo thanh toán từ cổng thanh toán SePay
    Endpoint này sẽ được gọi bởi cổng thanh toán khi có kết quả thanh toán
    """
    try:
        # Lấy dữ liệu từ webhook SePay
        payment_data = json.loads(request.body)
        logger.info(f"Nhận webhook từ SePay: {payment_data}")
        
        # Lưu thông tin giao dịch vào database (có thể tạo model Transaction)
        # Trong ví dụ PHP, họ lưu vào bảng tb_transactions
        transaction_fields = {
            'gateway': payment_data.get('gateway', ''),
            'transaction_date': payment_data.get('transactionDate', ''),
            'account_number': payment_data.get('accountNumber', ''),
            'transfer_type': payment_data.get('transferType', ''),
            'transfer_amount': payment_data.get('transferAmount', 0),
            'transaction_content': payment_data.get('content', ''),
            'reference_code': payment_data.get('referenceCode', ''),
            'description': payment_data.get('description', '')
        }
        
        # Log dữ liệu giao dịch để debug
        logger.info(f"Dữ liệu giao dịch: {transaction_fields}")
        
        # Trích xuất order_id từ nội dung chuyển khoản bằng regex
        # Mẫu mới: DH123-ABC123 -> 123 là order_id và ABC123 là transaction_uid
        import re
        content = payment_data.get('content', '')
        regex = r'DH(\d+)(?:-([A-Z0-9]+))?'
        matches = re.search(regex, content)
        
        if matches:
            # Nếu tìm thấy mã đơn hàng trong nội dung chuyển khoản
            order_id = matches.group(1)
            transaction_uid = matches.group(2) if len(matches.groups()) > 1 and matches.group(2) else None
            
            logger.info(f"Tìm thấy mã đơn hàng: {order_id}, mã giao dịch: {transaction_uid}")
            
            # Kiểm tra số tiền và trạng thái đơn hàng
            transfer_amount = payment_data.get('transferAmount', 0)
            
            try:
                with transaction.atomic():
                    # Tìm đơn hàng khớp với ID và trạng thái pending
                    order = Order.objects.select_for_update().get(
                        id=order_id,
                        status='pending'
                    )
                    
                    # Kiểm tra transaction_uid nếu có
                    if transaction_uid and hasattr(order, 'transaction_reference') and order.transaction_reference:
                        if order.transaction_reference != transaction_uid:
                            logger.warning(f"Mã giao dịch không khớp: Đơn hàng #{order_id}, Expected: {order.transaction_reference}, Actual: {transaction_uid}")
                            # Vẫn tiếp tục xác nhận nếu ID đơn hàng và số tiền khớp
                    
                    # Kiểm tra số tiền khớp với đơn hàng
                    expected_amount = float(order.total_amount)
                    actual_amount = float(transfer_amount)
                    
                    # Cho phép sai lệch 1% do làm tròn số
                    if abs(expected_amount - actual_amount) <= (expected_amount * 0.01):
                        # Cập nhật trạng thái đơn hàng thành completed
                        order.status = 'completed'
                        order.payment_status = 'completed'
                        order.transaction_id = payment_data.get('id') or payment_data.get('referenceCode')
                        order.save()
                        
                        # Cập nhật chi tiết đơn hàng
                        for item in order.items.all():
                            if not item.license_key:
                                item.license_key = f"SW-{order.id}-{item.product.id}-{secrets.token_hex(8).upper()}"
                                item.download_url = reverse('products:download', kwargs={'product_id': item.product.id, 'order_id': order.id})
                                item.save()
                        
                        # Xóa cache nếu có
                        cache.delete(f'payment_data_{order.id}')
                        cache.delete(f'order_{order.id}')
                        
                        # Gửi email thông báo (nếu cần)
                        # send_order_confirmation.delay(order.id)
                        
                        logger.info(f"Cập nhật thành công đơn hàng: {order_id}")
                        return JsonResponse({'success': True})
                    else:
                        logger.warning(f"Số tiền không khớp: Đơn hàng #{order_id}, Expected: {expected_amount}, Actual: {actual_amount}")
                        return JsonResponse({'success': False, 'message': 'Số tiền không khớp'})
            except Order.DoesNotExist:
                logger.warning(f"Không tìm thấy đơn hàng: {order_id}")
                return JsonResponse({'success': False, 'message': f'Không tìm thấy đơn hàng: {order_id}'}, status=404)
        else:
            logger.warning(f"Không tìm thấy mã đơn hàng trong nội dung: {content}")
            return JsonResponse({'success': False, 'message': 'Không tìm thấy mã đơn hàng'}, status=400)
    except json.JSONDecodeError:
        logger.error("Dữ liệu webhook không hợp lệ (JSON)")
        return JsonResponse({'success': False, 'message': 'Dữ liệu webhook không hợp lệ'}, status=400)
    except Exception as e:
        logger.error(f"Lỗi xử lý webhook: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}, status=500)

@login_required
def check_payment_status(request, order_id):
    """
    Kiểm tra trạng thái thanh toán của đơn hàng
    Endpoint này được gọi qua AJAX từ trang thanh toán
    """
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        
        # Nếu đơn hàng đã hoàn thành, trả về trạng thái completed
        if order.status == 'completed' or order.payment_status == 'completed':
            return JsonResponse({
                'status': 'completed',
                'message': _('Thanh toán đã hoàn thành'),
                'redirect_url': reverse('orders:detail', kwargs={'pk': order.id})
            })
        
        # Nếu đơn hàng bị hủy, trả về trạng thái cancelled
        if order.status == 'cancelled':
            return JsonResponse({
                'status': 'cancelled',
                'message': _('Đơn hàng đã bị hủy')
            })
            
        # Kiểm tra giao dịch từ SePay
        sepay = SePay()
        
        # Lọc giao dịch theo nội dung chuyển khoản tìm đơn hàng hiện tại
        reference = f"DH{order.id}"
        transactions = sepay.get_transactions_list({
            'transaction_date_min': order.created_at.strftime('%Y-%m-%d'),
            'limit': 20
        })
        
        if transactions['success'] and transactions.get('transactions'):
            # Lọc các giao dịch có nội dung chứa mã đơn hàng
            order_transactions = []
            for txn in transactions.get('transactions', []):
                content = txn.get('transaction_content', '')
                if reference in content:
                    order_transactions.append(txn)
            
            if order_transactions:
                # Tìm thấy giao dịch cho đơn hàng này
                latest_transaction = order_transactions[0]  # Giao dịch mới nhất
                
                # Lấy chi tiết giao dịch
                transaction_id = latest_transaction.get('id')
                transaction_details = sepay.verify_transaction(transaction_id)
                
                if transaction_details['success']:
                    # Kiểm tra số tiền
                    expected_amount = float(order.total_amount)
                    actual_amount = float(transaction_details.get('amount', 0))
                    
                    # Cho phép sai lệch 1% do làm tròn số
                    if abs(expected_amount - actual_amount) <= (expected_amount * 0.01):
                        # Cập nhật trạng thái đơn hàng
                        from django.db import transaction as db_transaction
                        with db_transaction.atomic():
                            order.status = 'completed'
                            order.payment_status = 'completed'
                            order.transaction_id = transaction_details.get('transaction_id')
                            order.save()
                            
                            # Cập nhật chi tiết đơn hàng
                            for item in order.items.all():
                                if not item.license_key:
                                    item.license_key = f"SW-{order.id}-{item.product.id}-{secrets.token_hex(8).upper()}"
                                    item.download_url = reverse('products:download', kwargs={'product_id': item.product.id, 'order_id': order.id})
                                    item.save()
                            
                            # Xóa cache
                            cache.delete(f'payment_data_{order.id}')
                            cache.delete(f'order_{order.id}')
                        
                        # Trả về trạng thái completed
                        return JsonResponse({
                            'status': 'completed',
                            'message': _('Thanh toán đã hoàn thành'),
                            'redirect_url': reverse('orders:detail', kwargs={'pk': order.id})
                        })
        
        # Đơn hàng vẫn đang xử lý, trả về trạng thái pending
        return JsonResponse({
            'status': 'pending',
            'message': _('Đơn hàng đang chờ thanh toán')
        })
    except Order.DoesNotExist:
        return JsonResponse({
            'status': 'error', 
            'message': _('Không tìm thấy đơn hàng')
        }, status=404)
    except Exception as e:
        logger.error(f"Lỗi kiểm tra trạng thái thanh toán cho đơn hàng {order_id}: {str(e)}")
        return JsonResponse({
            'status': 'error', 
            'message': _('Lỗi hệ thống')
        }, status=500)
