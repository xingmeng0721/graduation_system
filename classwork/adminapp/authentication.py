from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import AdminUser

from studentapp.models import Student
from teacherapp.models import teacher



class MultiModelBackend:
    """
    教师和学生认证后端 (最简版)。
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 如果调用时没有提供 'username' 参数，直接失败
        if username is None:
            return None

        # 1. 尝试在 teacher 表中查找
        try:
            user = teacher.objects.get(teacher_no=username)
            if user.check_password(password):
                return user
        except teacher.DoesNotExist:
            pass  # 找不到就继续

        # 2. 尝试在 student 表中查找
        try:
            user = Student.objects.get(stu_no=username)
            if user.check_password(password):
                return user
        except Student.DoesNotExist:
            pass  # 找不到就继续

        # 3. 所有尝试都失败
        return None

    def get_user(self, user_id):
        # 必须能找到教师或学生，以支持JWT令牌验证
        try:
            return teacher.objects.get(pk=user_id)
        except teacher.DoesNotExist:
            pass

        try:
            return Student.objects.get(pk=user_id)
        except Student.DoesNotExist:
            pass

        return None



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