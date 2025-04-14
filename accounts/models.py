from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.
class User(AbstractUser):
    """
    Mở rộng model User mặc định của Django
    """
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(_('phone number'), max_length=15, unique=True, null=True, blank=True)
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', null=True, blank=True)
    address = models.TextField(_('address'), null=True, blank=True)
    company_name = models.CharField(_('company name'), max_length=100, null=True, blank=True)
    company_website = models.URLField(_('company website'), null=True, blank=True)
    
    # Bắt buộc phải xác nhận email để sử dụng tài khoản
    is_email_verified = models.BooleanField(default=False)
    
    # Fields cho việc theo dõi
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='custom_user_set',  # Thêm related_name
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='custom_user_set',  # Thêm related_name
        related_query_name='user',
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def __str__(self):
        return self.username