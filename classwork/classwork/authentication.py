from rest_framework_simplejwt.authentication import JWTAuthentication
from adminapp.models import AdminUser
from studentapp.models import Student
from teacherapp.models import teacher


class UniversalJWTAuthentication(JWTAuthentication):
    """
    一个通用的JWT认证类，可以处理多种用户模型。
    它通过检查Token中的 'user_type' 字段来决定去哪个模型中查找用户。
    """
    def get_user(self, validated_token):
        try:
            user_id = validated_token['user_id']
            user_type = validated_token.get('user_type')
        except KeyError:
            return None  # Token中缺少必要信息

        if user_type == 'admin':
            try:
                user = AdminUser.objects.get(pk=user_id)
                # 为非标准用户动态添加 is_authenticated 属性
                user.is_authenticated = True
                return user
            except AdminUser.DoesNotExist:
                return None

        elif user_type == 'student':
            try:
                return Student.objects.get(pk=user_id)
            except Student.DoesNotExist:
                return None

        elif user_type == 'teacher':
            try:
                return teacher.objects.get(pk=user_id)
            except teacher.DoesNotExist:
                return None

        # 如果没有 user_type 或 user_type 不匹配，则认证失败
        return None