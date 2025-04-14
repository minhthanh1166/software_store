from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': _('Nhập địa chỉ email')
        })
    )
    username = forms.CharField(
        required=True,
        label=_('Tên đăng nhập'),
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': _('Nhập tên đăng nhập')
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        label=_('Số điện thoại'),
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': _('Nhập số điện thoại')
        })
    )
    password1 = forms.CharField(
        label=_('Mật khẩu'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': _('Nhập mật khẩu')
        }),
    )
    password2 = forms.CharField(
        label=_('Xác nhận mật khẩu'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': _('Nhập lại mật khẩu')
        }),
    )

    class Meta:
        model = User
        fields = ['email', 'username', 'phone_number', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError(_('Email không được để trống'))
            
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Email này đã được sử dụng'))
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            raise forms.ValidationError(_('Số điện thoại không được để trống'))
            
        if User.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError(_('Số điện thoại này đã được sử dụng'))
        return phone_number
        
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if not password1:
            raise forms.ValidationError(_('Mật khẩu không được để trống'))
        
        try:
            validate_password(password1, self.instance)
        except forms.ValidationError as error:
            self.add_error('password1', error)
        
        return password1
        
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_('Mật khẩu không khớp'))
        return password2
        
    def save(self, commit=True):
        # Đảm bảo email là field chính để đăng nhập
        user = super().save(commit=False)
        user.username = self.cleaned_data.get('username')
        user.email = self.cleaned_data.get('email')
        user.phone_number = self.cleaned_data.get('phone_number')
        # Khi sử dụng email là USERNAME_FIELD, ta cần đảm bảo email luôn được set
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'avatar', 
                 'address', 'company_name', 'company_website']
        labels = {
            'first_name': _('Tên'),
            'last_name': _('Họ'),
            'email': _('Email'),
            'phone_number': _('Số điện thoại'),
            'avatar': _('Ảnh đại diện'),
            'address': _('Địa chỉ'),
            'company_name': _('Tên công ty'),
            'company_website': _('Website công ty'),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'
            }) 