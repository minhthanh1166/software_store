import hashlib
import hmac
import json
import requests
import re
import os
from datetime import datetime
from django.conf import settings
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)

class SePay:
    """
    SePay payment gateway integration
    """
    def __init__(self):
        self.api_url = settings.SEPAY_BASE_URL
        self.merchant_id = settings.SEPAY_MERCHANT_ID
        self.api_key = settings.SEPAY_API_KEY
        self.secret_key = settings.SEPAY_SECRET_KEY
        self.bank_name = getattr(settings, 'SEPAY_BANK_NAME', 'MBBank')
        self.account_number = getattr(settings, 'SEPAY_ACCOUNT_NUMBER', 'VQRQACBCK3256')
        self.account_holder = getattr(settings, 'SEPAY_ACCOUNT_HOLDER', 'Bùi Minh Thành')

    def _generate_signature(self, data):
        """Tạo chữ ký số cho các giao dịch"""
        payload = json.dumps(data, sort_keys=True).encode('utf-8')
        signature = hmac.new(self.secret_key.encode('utf-8'), payload, hashlib.sha256).hexdigest()
        return signature

    def create_payment(self, payment_data):
        """
        Tạo yêu cầu thanh toán mới
        
        Tham số:
            payment_data: Có thể là một đối tượng Order hoặc dict chứa các thông tin thanh toán
        
        Trả về:
            dict: Thông tin thanh toán bao gồm dữ liệu mã QR và URL chuyển hướng
        """
        # Xử lý trường hợp payment_data là dict chứa thông tin thanh toán
        if isinstance(payment_data, dict):
            order_id = payment_data.get('order_id')
            amount = payment_data.get('amount')
            return_url = payment_data.get('return_url', settings.SEPAY_RETURN_URL)
            notify_url = payment_data.get('notify_url', settings.SEPAY_NOTIFY_URL)
            transfer_content = payment_data.get('transfer_content', f"DH{order_id}")
        else:
            # Xử lý trường hợp payment_data là đối tượng Order
            order_id = payment_data.id
            amount = float(payment_data.total_amount)
            return_url = settings.SEPAY_RETURN_URL
            notify_url = settings.SEPAY_NOTIFY_URL
            transfer_content = f"DH{order_id}"
        
        # Đảm bảo amount là số nguyên (VND không có phần thập phân)
        amount = int(amount)
        
        # Tạo dữ liệu thanh toán
        payment_info = {
            'order_id': order_id,
            'amount': amount,
            'qr_data': self.generate_qr_data(order_id, amount, transfer_content),
            'qr_url': self.generate_qr_url(order_id, amount, transfer_content),
            'payment_url': self.generate_payment_url(order_id, amount, return_url),
            'bank_name': self.bank_name,
            'account_number': self.account_number,
            'account_holder': self.account_holder,
            'transfer_content': transfer_content,
            'expires_in': 900,  # 15 phút (tính bằng giây)
            'status': 'pending'
        }
        
        return payment_info

    def generate_qr_url(self, order_id, amount, transfer_content=None):
        """Tạo URL cho ảnh QR thanh toán"""
        content = transfer_content or f"DH{order_id}"
        return f"https://qr.sepay.vn/img?bank={self.bank_name}&acc={self.account_number}&template=compact&amount={amount}&des={content}"

    def generate_qr_data(self, order_id, amount, transfer_content=None):
        """Tạo chuỗi dữ liệu QR code VietQR"""
        content = transfer_content or f"DH{order_id}"
        return f"sepay://pay/{order_id}?amount={amount}&content={content}"

    def generate_payment_url(self, order_id, amount, return_url):
        """Tạo URL trang thanh toán"""
        return f"{self.api_url}/pay/{order_id}?amount={amount}&return_url={return_url}"

    def verify_payment(self, data):
        """
        Xác thực thông báo thanh toán từ webhook
        
        Tham số:
            data (dict): Dữ liệu webhook từ SePay
            
        Trả về:
            dict: Thông tin đã xác thực
        """
        # Trích xuất mã đơn hàng từ content
        content = data.get('content', '')
        regex = r'DH(\d+)'
        matches = re.search(regex, content)
        
        if matches:
            order_id = matches.group(1)
            
            return {
                'success': True,
                'order_id': order_id,
                'transaction_id': data.get('id') or data.get('referenceCode'),
                'amount': data.get('transferAmount', 0),
                'content': content
            }
        
        # Nếu không tìm thấy mã đơn hàng trong nội dung
        return {
            'success': False,
            'message': 'Không tìm thấy mã đơn hàng trong nội dung thanh toán'
        }

    def query_transaction(self, transaction_id):
        """
        Truy vấn trạng thái giao dịch
        
        Tham số:
            transaction_id (str): Mã giao dịch
            
        Trả về:
            dict: Thông tin trạng thái giao dịch
        """
        # Giả lập truy vấn API thực tế
        # Trong môi trường thực tế, bạn sẽ gọi API của SePay để kiểm tra
        
        return {
            'success': True,
            'status': 'pending',  # Trạng thái có thể là: pending, paid, failed
            'amount': 0,
            'transaction_id': transaction_id
        }

    def verify_transaction(self, transaction_id):
        """
        Xác thực giao dịch sử dụng SePay API
        
        Tham số:
            transaction_id (str): Mã giao dịch cần xác thực
            
        Trả về:
            dict: Thông tin chi tiết giao dịch
        """
        try:
            # Lấy API key từ biến môi trường hoặc settings
            api_key = os.environ.get('SEPAY_USER_API_KEY', getattr(settings, 'SEPAY_USER_API_KEY', self.api_key))
            
            # Chuẩn bị headers với authorization
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Gọi API để lấy chi tiết giao dịch
            url = f"https://my.sepay.vn/userapi/transactions/details/{transaction_id}"
            response = requests.get(url, headers=headers)
            
            # Log response
            logger.info(f"SePay API response for transaction {transaction_id}: {response.status_code}")
            
            # Kiểm tra status code
            if response.status_code == 200:
                data = response.json()
                
                # Kiểm tra response thành công
                if data.get('status') == 200 and data.get('messages', {}).get('success'):
                    transaction = data.get('transaction', {})
                    
                    # Trích xuất mã đơn hàng từ nội dung chuyển khoản
                    content = transaction.get('transaction_content', '')
                    order_id = self.extract_order_id(content)
                    
                    return {
                        'success': True,
                        'status': 'completed', # Nếu API trả về được chi tiết giao dịch, coi như giao dịch đã hoàn thành
                        'order_id': order_id,
                        'transaction_id': transaction.get('id'),
                        'amount': float(transaction.get('amount_in', 0)),
                        'transaction_date': transaction.get('transaction_date'),
                        'content': content,
                        'account_number': transaction.get('account_number'),
                        'sub_account': transaction.get('sub_account'),
                        'bank_name': transaction.get('bank_brand_name'),
                        'reference_number': transaction.get('reference_number')
                    }
                
                # Response không thành công
                return {
                    'success': False,
                    'status': 'failed',
                    'message': data.get('error', 'Không thể xác thực giao dịch')
                }
            
            # Lỗi khi gọi API
            return {
                'success': False,
                'status': 'failed',
                'message': f'Lỗi API: {response.status_code}'
            }
            
        except Exception as e:
            logger.error(f"Lỗi khi xác thực giao dịch SePay: {str(e)}")
            return {
                'success': False,
                'status': 'error',
                'message': f'Lỗi hệ thống: {str(e)}'
            }

    def get_transactions_list(self, params=None):
        """
        Lấy danh sách giao dịch từ SePay API
        Chỉ lấy 3 giao dịch gần nhất để tối ưu tốc độ kiểm tra
        
        Tham số:
            params (dict): Các tham số truy vấn (account_number, transaction_date_min, transaction_date_max, etc.)
            
        Trả về:
            dict: Danh sách giao dịch
        """
        try:
            # Lấy API key từ biến môi trường hoặc settings
            api_key = os.environ.get('SEPAY_USER_API_KEY', getattr(settings, 'SEPAY_USER_API_KEY', self.api_key))
            
            # Chuẩn bị headers với authorization
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Chuẩn bị URL với các tham số
            url = "https://my.sepay.vn/userapi/transactions/list"
            if params is None:
                params = {}
                
            # Giới hạn chỉ lấy 3 giao dịch gần nhất
            params['limit'] = 3
            params['sort_by'] = 'created_at'
            params['sort_direction'] = 'desc'
            
            query_string = urlencode(params)
            url = f"{url}?{query_string}"
            
            # Gọi API
            response = requests.get(url, headers=headers)
            
            # Kiểm tra status code
            if response.status_code == 200:
                data = response.json()
                
                # Kiểm tra response thành công
                if data.get('status') == 200 and data.get('messages', {}).get('success'):
                    return {
                        'success': True,
                        'transactions': data.get('transactions', [])
                    }
                
                # Response không thành công
                return {
                    'success': False,
                    'message': data.get('error', 'Không thể lấy danh sách giao dịch')
                }
            
            # Lỗi khi gọi API
            return {
                'success': False,
                'message': f'Lỗi API: {response.status_code}'
            }
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy danh sách giao dịch SePay: {str(e)}")
            return {
                'success': False,
                'message': f'Lỗi hệ thống: {str(e)}'
            }

    def extract_order_id(self, content):
        """
        Trích xuất ID đơn hàng từ nội dung thanh toán
        
        Định dạng mặc định: DH123 -> 123 là order_id
        """
        regex = r'DH(\d+)'
        matches = re.search(regex, content)
        
        if matches:
            return matches.group(1)
        
        return None

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