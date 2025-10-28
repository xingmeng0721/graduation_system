from django.urls import path, include
from rest_framework.routers import DefaultRouter
from teamapp.views import TeamViewSet

router = DefaultRouter()
router.register(r'', TeamViewSet, basename='team')

urlpatterns = [
    path('', include(router.urls)),
]