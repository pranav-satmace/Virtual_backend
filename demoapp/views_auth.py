# yourapp/views_auth.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenViewBase
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers

from .serializers_auth import RegisterWithEmailSerializer, VerifyEmailOTPSerializer
from .models import UserProfile

class RegisterWithEmailView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        ser = RegisterWithEmailSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        profile = ser.save()
        return Response({
            'message': 'User created. OTP sent to email.',
            'email': profile.user.email
        }, status=status.HTTP_201_CREATED)

class VerifyEmailOTPView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        ser = VerifyEmailOTPSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.save()
        return Response(data, status=status.HTTP_200_OK)

class PatchedTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        profile = UserProfile.objects.get(user=user)
        if not profile.email_verified:
            raise serializers.ValidationError('Email not verified')
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        return token

class PatchedTokenObtainPairView(TokenViewBase):
    permission_classes = [AllowAny]
    serializer_class = PatchedTokenObtainPairSerializer

class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({'detail': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)
