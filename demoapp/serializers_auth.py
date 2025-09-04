# yourapp/serializers_auth.py
from django.contrib.auth.models import User
from rest_framework import serializers
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile
from .utils import send_email_otp


class RegisterWithEmailSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({'email': 'Already registered'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data['email']
        name = validated_data['name']
        password = validated_data['password']

     # Use email as username (unique constraint problem solved ✅)
        user = User(
            username=email,
            email= email,
            first_name= name,
            is_active=True  # user stays active, we’ll check email_verified later
        )
        user.set_password(password)
        user.save()

        profile = UserProfile.objects.create(user=user)  # tenant left NULL
        profile.generate_email_otp()
        send_email_otp(user.email, profile.email_otp)
        return profile

# class RegisterWithEmailSerializer(serializers.Serializer):
#     username = serializers.CharField()
#     email = serializers.EmailField()
#     password = serializers.CharField(write_only=True, min_length=8)

#     def validate(self, attrs):
#         if User.objects.filter(username=attrs['username']).exists():
#             raise serializers.ValidationError({'username': 'Already taken'})
#         if User.objects.filter(email=attrs['email']).exists():
#             raise serializers.ValidationError({'email': 'Already registered'})
#         return attrs

#     @transaction.atomic
#     def create(self, validated_data):
#         user = User(
#             username=validated_data['username'],
#             email=validated_data['email'],
#             is_active=True  # user stays active, we’ll check email_verified later
#         )
#         user.set_password(validated_data['password'])
#         user.save()

#         profile = UserProfile.objects.create(user=user)  # tenant left NULL
#         profile.generate_email_otp()
#         send_email_otp(user.email, profile.email_otp)
#         return profile

class VerifyEmailOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': 'User not found'})
        attrs['user'] = user
        return attrs

    def create_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {'refresh': str(refresh), 'access': str(refresh.access_token)}

    def save(self, **kwargs):
        user: User = self.validated_data['user']
        profile = UserProfile.objects.get(user=user)
        otp = self.validated_data['otp']
        if not profile.verify_email_otp(otp):
            raise serializers.ValidationError({'otp': 'Invalid or expired'})
        return {
            'user_id': user.id,
            'tokens': self.create_tokens(user)
        }
