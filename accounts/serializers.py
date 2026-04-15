from rest_framework import serializers
from .models import Account


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