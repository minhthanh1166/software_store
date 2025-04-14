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
        
    error_message = None
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me') == 'on'
        
        if not email or not password:
            error_message = _('Vui lòng nhập cả email và mật khẩu')
            messages.error(request, error_message)
        else:
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user)
                
                # Nếu không chọn "Ghi nhớ đăng nhập", session sẽ hết hạn khi đóng trình duyệt
                if not remember_me:
                    request.session.set_expiry(0)
                    
                messages.success(request, _('Đăng nhập thành công'))
                
                # Chuyển hướng đến trang được yêu cầu nếu có
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('products:list')
            else:
                error_message = _('Email hoặc mật khẩu không đúng')
                messages.error(request, error_message)
                
                # Log debug info
                print(f"Login failed for email: {email}")
                
                # Thử tìm user với email này để kiểm tra
                try:
                    user_exists = User.objects.filter(email=email).exists()
                    if user_exists:
                        print(f"User with email {email} exists but authentication failed - password may be incorrect")
                    else:
                        print(f"No user found with email {email}")
                except Exception as e:
                    print(f"Error checking user: {str(e)}")
    
    return render(request, 'accounts/login.html', {'error_message': error_message})

def logout_view(request):
    # Lưu thông báo trước khi đăng xuất
    messages.success(request, _('Đăng xuất thành công'))
    
    # Thực hiện đăng xuất
    logout(request)
    
    # Xóa mọi cookie liên quan đến session
    response = redirect('products:list')
    if 'sessionid' in request.COOKIES:
        response.delete_cookie('sessionid')
    if 'csrftoken' in request.COOKIES:
        response.delete_cookie('csrftoken')
    
    return response

def register(request):
    if request.user.is_authenticated:
        return redirect('products:list')
        
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Auto-login sau khi đăng ký thành công
                # login(request, user)
                
                # Log thông tin tài khoản mới tạo để debug
                print(f"User created successfully: {user.email}, username: {user.username}")
                
                messages.success(request, _('Tài khoản của bạn đã được tạo thành công! Bạn có thể đăng nhập ngay bây giờ.'))
                return redirect('accounts:login')
            except Exception as e:
                # Log lỗi
                print(f"Error creating user: {str(e)}")
                messages.error(request, _('Có lỗi xảy ra khi tạo tài khoản. Vui lòng thử lại.'))
        else:
            # Log lỗi form
            print(f"Form errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegisterForm()
        
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _('Thông tin của bạn đã được cập nhật thành công!'))
                return redirect('accounts:profile')
            except Exception as e:
                print(f"Error updating profile: {str(e)}")
                messages.error(request, _('Có lỗi xảy ra khi cập nhật thông tin. Vui lòng thử lại.'))
        else:
            print(f"Form errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
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