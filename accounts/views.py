from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import User
from .forms import UserRegisterForm, UserProfileForm

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

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Tài khoản của bạn đã được tạo thành công! Bạn có thể đăng nhập ngay bây giờ.'))
            return redirect('accounts:login')
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'accounts/profile.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Thông tin của bạn đã được cập nhật thành công!'))
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})

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