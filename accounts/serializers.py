from rest_framework import serializers
from .models import Account,UserToken
from django.utils import timezone
from django.shortcuts import get_object_or_404
import hashlib

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Account
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'role']

  
    def validate_email(self, value):
        if Account.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

  
    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters")
        return value

 
    def validate_role(self, value):
        if value not in ['student', 'instructor']:
            raise serializers.ValidationError("Invalid role")
        return value

   
    def create(self, validated_data):
        password = validated_data.pop("password")

        user = Account(**validated_data)
        user.set_password(password)  
        user.save()

        return user




class RequestPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token_type = serializers.CharField()

    def validate_email(self, value):
        if not Account.objects.filter(email=value).exists():
            raise serializers.ValidationError("No account with this email")

        
        active_token = UserToken.objects.filter(
            user__email=value,
            is_used=False,
            expires_at__gt=timezone.now()
        ).exists()

        if active_token:
            raise serializers.ValidationError(
                "Reset request already exists. Please check your email."
            )

        return value

    def validate_token_type(self, value):
        if value not in ["reset_password", "email_verification"]:
            raise serializers.ValidationError("Invalid token type")
        return value
    



class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)

    def validate_token(self, value):
        if not value:
            raise serializers.ValidationError("Token is required to change password")

        raw_token = str(value)
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()

        active_request = UserToken.objects.filter(
            token=hashed_token,
            is_used=False
        ).first()

        if not active_request:
            raise serializers.ValidationError(
                "Reset request does not exist or already used"
            )

        if active_request.expires_at < timezone.now():
            raise serializers.ValidationError(
                "Token expired, please regenerate it"
            )

        self.context["token_obj"] = active_request

        return value

    def validate_password(self, value):
        if not value:
            raise serializers.ValidationError("Password is required")

        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters"
            )

        return value


    def validate_confirm_password(self, value):
        if not value:
            raise serializers.ValidationError("Confirm password is required")
        return value

    def validate(self, data):
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        if password != confirm_password:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match"
            })

        data["token_obj"] = self.context.get("token_obj")

        return data
