from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import AdminUser

# class CustomJWTAuthentication(JWTAuthentication):
#     """
#     自定义JWT认证类，用于适配未继承Django User的自定义用户模型。
#     """
#     def get_user(self, validated_token):
#         """
#         重写 get_user 方法。
#         当Token验证通过后，此方法被调用以获取用户对象。
#         """
#         try:
#             # 从Token的载荷(payload)中获取'user_id'
#             user_id = validated_token['user_id']
#         except KeyError:
#             # 如果Token中没有'user_id'，则认证失败
#             return None
#
#         try:
#             # 使用获取到的user_id，直接查询我们的AdminUser模型
#             user = AdminUser.objects.get(pk=user_id)
#         except AdminUser.DoesNotExist:
#             # 如果数据库中不存在该用户，则认证失败
#             return None
#
#         user.is_authenticated = True
#
#         # 成功获取用户对象并返回
#         return user


from django.contrib.auth.hashers import check_password
from .models import AdminUser


class AdminUserBackend:
    """
    用于在登录时验证管理员的认证后端。
    """
    def authenticate(self, request, admin_username=None, password=None, **kwargs):
        try:
            user = AdminUser.objects.get(admin_username=admin_username)
            if user and check_password(password, user.admin_password):
                return user
        except AdminUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return AdminUser.objects.get(pk=user_id)
        except AdminUser.DoesNotExist:
            return None