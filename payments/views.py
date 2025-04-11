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
