# yourapp/views_auth.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenViewBase, TokenRefreshView
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
        
        # 🔄 reorder tokens: access first, refresh second
        # return Response({
        #     "access": data['tokens']['access'],
        #     "refresh": data['tokens']['refresh'],
        #     "user_id": data['user_id'],
        # }, status=status.HTTP_200_OK)


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

# class PatchedTokenObtainPairView(TokenViewBase):
#     permission_classes = [AllowAny]
#     serializer_class = PatchedTokenObtainPairSerializer
class PatchedTokenObtainPairView(TokenViewBase):
    permission_classes = [AllowAny]
    serializer_class = PatchedTokenObtainPairSerializer

    #  reorder tokens in response
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            data = response.data
            response.data = {
                "access": data.get("access"),
                "refresh": data.get("refresh"),
            }
        return response


class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    #  reorder tokens in response
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            data = response.data
            response.data = {
                "access": data.get("access"),
                "refresh": request.data.get("refresh"),  # keep refresh in output too
            }
        return response
    
    
class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({'detail': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)
