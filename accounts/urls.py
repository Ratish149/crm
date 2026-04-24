from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import MyTokenObtainPairView, RegisterView, UserRetrieveUpdateDestroyAPIView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "users/<int:pk>/",
        UserRetrieveUpdateDestroyAPIView.as_view(),
        name="user-detail",
    ),
]
