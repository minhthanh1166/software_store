from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db import transaction
from .models import Payment, Refund
from orders.models import Order
from .forms import PaymentForm, RefundForm
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from .sepay import SePay

class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'payments/payment_list.html'
    context_object_name = 'payments'

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = Payment
    template_name = 'payments/payment_detail.html'
    context_object_name = 'payment'

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

class PaymentCreateView(LoginRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'payments/payment_form.html'
    success_url = reverse_lazy('payments:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.kwargs.get('order_id')
        order = get_object_or_404(Order, id=order_id, user=self.request.user)
        context['order'] = order
        return context

    def form_valid(self, form):
        order_id = self.kwargs.get('order_id')
        order = get_object_or_404(Order, id=order_id, user=self.request.user)
        
        if order.payment_status:
            messages.error(self.request, _('This order has already been paid'))
            return redirect('orders:detail', pk=order.id)
        
        payment = form.save(commit=False)
        payment.order = order
        payment.user = self.request.user
        payment.amount = order.total_amount
        
        # Simulate payment processing
        payment.status = 'completed'
        payment.save()
        
        # Update order status
        order.payment_status = True
        order.status = 'processing'
        order.save()
        
        messages.success(self.request, _('Payment completed successfully'))
        return super().form_valid(form)

class RefundCreateView(LoginRequiredMixin, CreateView):
    model = Refund
    form_class = RefundForm
    template_name = 'payments/refund_form.html'
    success_url = reverse_lazy('payments:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment_id = self.kwargs.get('payment_id')
        payment = get_object_or_404(Payment, id=payment_id, user=self.request.user)
        context['payment'] = payment
        return context

    def form_valid(self, form):
        payment_id = self.kwargs.get('payment_id')
        payment = get_object_or_404(Payment, id=payment_id, user=self.request.user)
        
        if payment.status != 'completed':
            messages.error(self.request, _('Only completed payments can be refunded'))
            return redirect('payments:detail', pk=payment.id)
        
        refund = form.save(commit=False)
        refund.payment = payment
        refund.amount = payment.amount
        refund.save()
        
        messages.success(self.request, _('Refund request submitted successfully'))
        return super().form_valid(form)

@login_required
def process_refund(request, refund_id):
    refund = get_object_or_404(Refund, id=refund_id, payment__user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            refund.status = 'approved'
            refund.payment.status = 'refunded'
            refund.payment.save()
            refund.save()
            messages.success(request, _('Refund approved'))
        elif action == 'reject':
            refund.status = 'rejected'
            refund.save()
            messages.success(request, _('Refund rejected'))
        
        return redirect('payments:detail', pk=refund.payment.id)
    
    return render(request, 'payments/process_refund.html', {
        'refund': refund
    })

@login_required
def checkout(request, order_id):
    """Xử lý thanh toán đơn hàng phần mềm"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status != 'pending':
        messages.error(request, 'Đơn hàng này không thể thanh toán.')
        return redirect('orders:detail', order_id=order.id)
    
    # Khởi tạo SePay
    sepay = SePay()
    
    # Tạo yêu cầu thanh toán
    payment_result = sepay.create_payment(order)
    
    if payment_result['success']:
        # Lưu thông tin thanh toán
        payment = Payment.objects.create(
            order=order,
            user=request.user,
            amount=order.total_amount,
            payment_method='sepay',
            transaction_id=payment_result['transaction_id'],
            status='pending'
        )
        
        # Chuyển hướng đến trang thanh toán
        return redirect(payment_result['payment_url'])
    else:
        messages.error(request, 'Không thể khởi tạo thanh toán. Vui lòng thử lại sau.')
        return redirect('orders:detail', order_id=order.id)

@csrf_exempt
def payment_notify(request):
    """Xử lý thông báo kết quả thanh toán từ SePay"""
    if request.method == 'POST':
        sepay = SePay()
        notification_data = request.POST.dict()
        
        # Xác thực thông báo
        verify_result = sepay.verify_payment(notification_data)
        
        if verify_result['success']:
            with transaction.atomic():
                # Cập nhật trạng thái đơn hàng và thanh toán
                order = get_object_or_404(Order, id=verify_result['order_id'])
                payment = get_object_or_404(Payment, order=order)
                
                if verify_result['status'] == 'success':
                    # Thanh toán thành công - kích hoạt license ngay
                    order.status = 'completed'
                    payment.status = 'completed'
                    
                    # Tạo và kích hoạt license keys cho các sản phẩm
                    for item in order.items.all():
                        item.product.generate_license(order.user)
                        
                elif verify_result['status'] == 'failed':
                    order.status = 'cancelled'
                    payment.status = 'failed'
                
                order.save()
                payment.save()
            
            return HttpResponse('OK')
    
    return HttpResponse('Failed', status=400)

@login_required
def payment_return(request):
    """Xử lý khi người dùng quay lại từ trang thanh toán"""
    order_id = request.GET.get('orderId')
    status = request.GET.get('status')
    
    if order_id:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        payment = get_object_or_404(Payment, order=order)
        
        if status == 'success':
            messages.success(request, 'Thanh toán thành công! Bạn có thể tải phần mềm ngay bây giờ.')
            return redirect('payments:payment_result', payment_id=payment.id)
        elif status == 'pending':
            messages.info(request, 'Thanh toán đang được xử lý. Chúng tôi sẽ thông báo khi có kết quả.')
            return redirect('payments:payment_result', payment_id=payment.id)
        else:
            messages.error(request, 'Thanh toán không thành công. Vui lòng thử lại sau.')
            return redirect('orders:detail', order_id=order.id)
    
    messages.error(request, 'Không tìm thấy thông tin đơn hàng.')
    return redirect('orders:list')

@login_required
def payment_cancel(request):
    """Xử lý khi người dùng hủy thanh toán"""
    order_id = request.GET.get('orderId')
    
    if order_id:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        messages.info(request, 'Bạn đã hủy thanh toán. Vui lòng thử lại khi cần.')
        return redirect('order_detail', order_id=order.id)
    
    messages.error(request, 'Không tìm thấy thông tin đơn hàng.')
    return redirect('orders')

@login_required
def refund_request(request, order_id):
    """Xử lý yêu cầu hoàn tiền"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, user=request.user, status='completed')
        payment = get_object_or_404(Payment, order=order, status='completed')
        
        reason = request.POST.get('reason')
        if not reason:
            messages.error(request, 'Vui lòng cung cấp lý do hoàn tiền.')
            return redirect('order_detail', order_id=order.id)
        
        sepay = SePay()
        refund_result = sepay.refund_transaction(
            payment.transaction_id,
            order.total_amount,
            reason
        )
        
        if refund_result['success']:
            order.status = 'refunded'
            payment.status = 'refunded'
            order.save()
            payment.save()
            
            messages.success(request, 'Yêu cầu hoàn tiền đã được xử lý thành công.')
        else:
            messages.error(request, 'Không thể xử lý yêu cầu hoàn tiền. Vui lòng thử lại sau.')
        
        return redirect('order_detail', order_id=order.id)
    
    return redirect('orders')
