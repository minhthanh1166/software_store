from django.conf import settings
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site

class SePay:
    """
    Tích hợp cổng thanh toán SePay (giả lập)
    Trong ứng dụng thực tế, lớp này sẽ tích hợp với cổng thanh toán thật
    """
    def __init__(self):
        # Trong môi trường production, các thông số này sẽ được lấy từ Django settings
        self.api_key = getattr(settings, 'SEPAY_API_KEY', 'test_key')
        self.api_secret = getattr(settings, 'SEPAY_API_SECRET', 'test_secret')
        self.base_url = getattr(settings, 'SEPAY_BASE_URL', 'https://sepay.example.com')

    def create_payment(self, payment_data):
        """
        Tạo yêu cầu thanh toán và trả về URL thanh toán
        Trong triển khai thực tế, hàm này sẽ gọi API đến cổng thanh toán
        
        Tham số:
            payment_data (dict): Chứa order_id, amount, return_url, và notify_url
        
        Trả về:
            dict: Thông tin thanh toán bao gồm dữ liệu mã QR và URL chuyển hướng
        """
        order_id = payment_data['order_id']
        amount = payment_data['amount']
        return_url = payment_data.get('return_url', '')
        
        # Tạo dữ liệu thanh toán cho SePay (giả lập)
        base_url = getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')
        
        # URL tuyệt đối cho trang thanh toán SePay
        payment_url = f"{self.base_url}/pay/{order_id}?amount={amount}&return_url={return_url}"
        
        # Tạo dữ liệu QR để sử dụng trong ứng dụng SePay 
        qr_data = f"sepay://pay/{order_id}?amount={amount}"
        
        return {
            'payment_url': payment_url,
            'qr_data': qr_data,
            'amount': amount,
            'order_id': order_id,
            'expires_in': 900,  # 15 phút (tính bằng giây)
            'status': 'pending'
        }

    def verify_payment(self, payment_data):
        """
        Xác minh thông báo thanh toán
        Trong triển khai thực tế, hàm này sẽ xác minh chữ ký và trạng thái thanh toán
        
        Tham số:
            payment_data (dict): Dữ liệu thông báo thanh toán từ cổng thanh toán
        
        Trả về:
            dict: Thông tin thanh toán đã xác minh
        """
        # Triển khai giả lập - luôn trả về thành công để kiểm thử
        return {
            'status': 'success',
            'order_id': payment_data.get('order_id'),
            'amount': payment_data.get('amount'),
            'transaction_id': f"SEPAY-{payment_data.get('order_id')}-{payment_data.get('amount', 0)}"
        } 