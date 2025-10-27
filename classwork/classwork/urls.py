from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # 将所有 /api/ 开头的请求都路由到 adminapp.urls
    path('api/admin/', include('adminapp.urls')),
    # 所有 /api/student/ 开头的 URL 交给 studentapp 处理 (学生相关)
    path("api/student/", include("studentapp.urls")),

    path("api/teacher/", include("teacherapp.urls")),
]
#api/student/login/