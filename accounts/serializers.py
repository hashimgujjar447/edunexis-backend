from rest_framework import serializers
from .models import Account, UserToken
from django.utils import timezone
import hashlib



# 🔐 helper
def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


# 🔐 REGISTER
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Account
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'role']

    def validate_email(self, value):
        value = value.lower()
        user = Account.objects.filter(email=value).first()

        if user and user.is_active:
            raise serializers.ValidationError("Account already exists")

        return value

    def validate_role(self, value):
        if value not in ['student', 'instructor']:
            raise serializers.ValidationError("Invalid role")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = Account.objects.filter(email=validated_data["email"]).first()

        if user:
            
            for attr, val in validated_data.items():
                setattr(user, attr, val)
        else:
            user = Account(**validated_data)

        user.set_password(password)
        user.is_active = False
        user.save()

        return user


class RequestRegisterationCodeSerializer(serializers.Serializer):
    email=serializers.EmailField()
    

    def validate_email(self,value):
        
        return value.lower()
  
    


class RequestPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token_type = serializers.CharField()

    def validate(self, data):
        email = data.get("email").lower()
        token_type = data.get("token_type")

        if token_type not in ["reset_password", "email_verification"]:
            raise serializers.ValidationError({"token_type": "Invalid token type"})

        active_token = UserToken.objects.filter(
            user__email=email,
            token_type=token_type,
            is_used=False,
            expires_at__gt=timezone.now()
        ).exists()

        if active_token:
            raise serializers.ValidationError(
                {"message": "Request already exists. Please check your email."}
            )

        data["email"] = email
        return data


# 🔐 PASSWORD RESET CONFIRM
class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField()

    def validate(self, data):
        raw_token = data.get("token")
        hashed_token = hash_token(raw_token)

        token_obj = UserToken.objects.filter(
            token=hashed_token,
            token_type="reset_password",   # 🔥 FIXED
            is_used=False
        ).first()

        if not token_obj:
            raise serializers.ValidationError(
                {"token": "Invalid or used token"}
            )

        if token_obj.expires_at < timezone.now():
            raise serializers.ValidationError(
                {"token": "Token expired"}
            )

        if data.get("password") != data.get("confirm_password"):
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match"}
            )

        data["token_obj"] = token_obj
        return data



class RegisterationTokenVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(
        error_messages={
            "required": "Email is required",
            "invalid": "Enter a valid email address"
        }
    )
    code = serializers.CharField(
        min_length=6,
        max_length=6,
        error_messages={
            "required": "Code is required",
            "blank": "Code cannot be empty",
            "min_length": "Code must be 6 digits",
            "max_length": "Code must be 6 digits"
        }
    )

    def validate_email(self, value):
        return value.lower()