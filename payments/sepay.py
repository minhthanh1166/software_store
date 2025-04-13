import hashlib
import hmac
import json
import requests
from datetime import datetime
from django.conf import settings
from urllib.parse import urlencode

class SePay:
    def __init__(self):
        self.merchant_id = settings.SEPAY_MERCHANT_ID
        self.api_key = settings.SEPAY_API_KEY
        self.api_secret = settings.SEPAY_API_SECRET
        self.api_url = 'https://api.sepay.vn/v1' if not settings.DEBUG else 'https://sandbox.sepay.vn/v1'

    def _generate_signature(self, data):
        """Tạo chữ ký số cho request"""
        sorted_data = dict(sorted(data.items()))
        message = '&'.join([f"{k}={v}" for k, v in sorted_data.items()])
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    def create_payment(self, order):
        """Tạo yêu cầu thanh toán mới"""
        data = {
            'merchantId': self.merchant_id,
            'orderId': str(order.id),
            'amount': int(order.total_amount),
            'description': f'Thanh toán đơn hàng #{order.id}',
            'returnUrl': settings.SEPAY_RETURN_URL,
            'notifyUrl': settings.SEPAY_NOTIFY_URL,
            'cancelUrl': settings.SEPAY_CANCEL_URL,
            'timestamp': int(datetime.now().timestamp()),
            'currency': 'VND',
            'language': 'vi',
        }

        # Tạo chữ ký số
        signature = self._generate_signature(data)
        data['signature'] = signature

        # Gọi API tạo thanh toán
        headers = {
            'Content-Type': 'application/json',
            'X-API-KEY': self.api_key
        }
        
        response = requests.post(
            f'{self.api_url}/payment/create',
            json=data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['status'] == 'success':
                return {
                    'success': True,
                    'payment_url': result['data']['paymentUrl'],
                    'transaction_id': result['data']['transactionId']
                }
        
        return {
            'success': False,
            'message': 'Không thể tạo yêu cầu thanh toán'
        }

    def verify_payment(self, data):
        """Xác thực kết quả thanh toán từ SePay"""
        received_signature = data.pop('signature', '')
        calculated_signature = self._generate_signature(data)
        
        if hmac.compare_digest(received_signature, calculated_signature):
            return {
                'success': True,
                'order_id': data['orderId'],
                'transaction_id': data['transactionId'],
                'amount': data['amount'],
                'status': data['status']
            }
        
        return {
            'success': False,
            'message': 'Chữ ký không hợp lệ'
        }

    def query_transaction(self, transaction_id):
        """Truy vấn trạng thái giao dịch"""
        data = {
            'merchantId': self.merchant_id,
            'transactionId': transaction_id,
            'timestamp': int(datetime.now().timestamp())
        }
        
        signature = self._generate_signature(data)
        data['signature'] = signature
        
        headers = {
            'Content-Type': 'application/json',
            'X-API-KEY': self.api_key
        }
        
        response = requests.post(
            f'{self.api_url}/payment/query',
            json=data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['status'] == 'success':
                return {
                    'success': True,
                    'status': result['data']['status'],
                    'amount': result['data']['amount'],
                    'transaction_id': result['data']['transactionId']
                }
        
        return {
            'success': False,
            'message': 'Không thể truy vấn giao dịch'
        }

    def refund_transaction(self, transaction_id, amount, reason):
        """Hoàn tiền giao dịch"""
        data = {
            'merchantId': self.merchant_id,
            'transactionId': transaction_id,
            'amount': amount,
            'reason': reason,
            'timestamp': int(datetime.now().timestamp())
        }
        
        signature = self._generate_signature(data)
        data['signature'] = signature
        
        headers = {
            'Content-Type': 'application/json',
            'X-API-KEY': self.api_key
        }
        
        response = requests.post(
            f'{self.api_url}/payment/refund',
            json=data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['status'] == 'success':
                return {
                    'success': True,
                    'refund_id': result['data']['refundId'],
                    'status': result['data']['status']
                }
        
        return {
            'success': False,
            'message': 'Không thể hoàn tiền giao dịch'
        } 