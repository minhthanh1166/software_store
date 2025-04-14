from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailBackend(ModelBackend):
    """
    Backend xác thực cho phép đăng nhập bằng email/password
    """
    def authenticate(self, request, email=None, password=None, **kwargs):
        UserModel = get_user_model()
        
        # Ghi log để debug
        print(f"EmailBackend: Authenticating with email={email}")
        
        try:
            # Tìm user bằng email
            user = UserModel.objects.get(email=email)
            
            # Kiểm tra mật khẩu
            if user.check_password(password):
                print(f"EmailBackend: Authentication successful for email={email}")
                return user
            else:
                print(f"EmailBackend: Password incorrect for email={email}")
        except UserModel.DoesNotExist:
            print(f"EmailBackend: No user found with email={email}")
            return None
        except Exception as e:
            print(f"EmailBackend: Authentication error: {str(e)}")
            return None 