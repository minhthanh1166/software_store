from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import User

def login_view(request):
    if request.user.is_authenticated:
        return redirect('products:list')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me') == 'on'
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            
            # Nếu không chọn "Ghi nhớ đăng nhập", session sẽ hết hạn khi đóng trình duyệt
            if not remember_me:
                request.session.set_expiry(0)
                
            messages.success(request, _('Đăng nhập thành công'))
            return redirect('products:list')
        else:
            messages.error(request, _('Email hoặc mật khẩu không đúng'))
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, _('Đăng xuất thành công'))
    return redirect('products:list')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('products:list')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        # Kiểm tra mật khẩu
        if password != password2:
            messages.error(request, _('Mật khẩu xác nhận không khớp'))
            return render(request, 'accounts/register.html')
        
        # Kiểm tra email đã tồn tại chưa
        if User.objects.filter(email=email).exists():
            messages.error(request, _('Email đã được sử dụng'))
            return render(request, 'accounts/register.html')
        
        # Kiểm tra username đã tồn tại chưa
        if User.objects.filter(username=username).exists():
            messages.error(request, _('Tên người dùng đã được sử dụng'))
            return render(request, 'accounts/register.html')
        
        # Kiểm tra số điện thoại đã tồn tại chưa
        if User.objects.filter(phone_number=phone_number).exists():
            messages.error(request, _('Số điện thoại đã được sử dụng'))
            return render(request, 'accounts/register.html')
        
        # Tạo user mới
        user = User.objects.create_user(
            username=username,
            email=email,
            phone_number=phone_number,
            password=password
        )
        
        # Đăng nhập sau khi đăng ký
        login(request, user)
        messages.success(request, _('Đăng ký thành công'))
        return redirect('products:list')
    
    return render(request, 'accounts/register.html')

@login_required
def profile_view(request):
    user = request.user
    
    if request.method == 'POST':
        # Cập nhật thông tin người dùng
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.phone_number = request.POST.get('phone_number', '')
        user.address = request.POST.get('address', '')
        user.company_name = request.POST.get('company_name', '')
        user.company_website = request.POST.get('company_website', '')
        
        # Cập nhật avatar nếu có
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
        
        user.save()
        messages.success(request, _('Thông tin cá nhân đã được cập nhật'))
        return redirect('accounts:profile')
    
    return render(request, 'accounts/profile.html')

@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Kiểm tra mật khẩu hiện tại
        if not request.user.check_password(current_password):
            messages.error(request, _('Mật khẩu hiện tại không đúng'))
            return redirect('accounts:profile')
        
        # Kiểm tra mật khẩu mới khớp với xác nhận
        if new_password != confirm_password:
            messages.error(request, _('Mật khẩu mới không khớp với xác nhận'))
            return redirect('accounts:profile')
        
        # Đổi mật khẩu
        request.user.set_password(new_password)
        request.user.save()
        
        # Cập nhật session để không bị đăng xuất
        update_session_auth_hash(request, request.user)
        
        messages.success(request, _('Mật khẩu đã được thay đổi'))
        return redirect('accounts:profile')
    
    return redirect('accounts:profile')