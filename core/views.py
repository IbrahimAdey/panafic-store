from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from django.contrib.auth import authenticate
from datetime import timedelta
from .serializers import RegisterSerializer, LoginSerializer
from .models import User
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Generate token with correct expiry
            refresh = RefreshToken.for_user(user)
            if user.role == 'merchant':
                refresh.access_token.set_exp(lifetime=timedelta(days=7))
            else:
                refresh.access_token.set_exp(lifetime=timedelta(days=1))

            return Response({
                "error": False,
                "message": "User registered successfully",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "country": user.country,
                    "base_currency": user.base_currency,
                    "full_name": user.full_name
                },
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }, status=status.HTTP_201_CREATED)
        return Response({
            "error": True,
            "message": "Validation error",
            "field": list(serializer.errors.keys())[0] if serializer.errors else None
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True))
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(email=serializer.validated_data['email'],
                              password=serializer.validated_data['password'])
            if user:
                refresh = RefreshToken.for_user(user)
                if user.role == 'merchant':
                    refresh.access_token.set_exp(lifetime=timedelta(days=7))
                else:
                    refresh.access_token.set_exp(lifetime=timedelta(days=1))

                return Response({
                    "error": False,
                    "message": "Login successful",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "role": user.role,
                        "country": user.country,
                        "base_currency": user.base_currency,
                        "full_name": user.full_name
                    },
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                })
            return Response({"error": True, "message": "Invalid credentials"}, status=401)
        return Response({
            "error": True,
            "message": "Validation error",
            "field": list(serializer.errors.keys())[0]
        }, status=400)