from rest_framework import serializers
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'password', 'full_name', 'role', 'country', 'base_currency']

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            role=validated_data['role'],
            country=validated_data['country'],
            base_currency=validated_data['base_currency'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)