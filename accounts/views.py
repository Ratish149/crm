from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from crm.utils import CustomPagination

from .serializers import (
    MyTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(generics.ListCreateAPIView):
    queryset = User.objects.all().order_by("-date_joined")
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method == "GET":
            return UserSerializer
        return RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            refresh["is_superuser"] = user.is_superuser
            return Response(
                {
                    "user": UserSerializer(user).data,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "message": "User created successfully.",
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class UserRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    lookup_field = "pk"
