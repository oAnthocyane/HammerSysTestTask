from rest_framework import serializers
from typing_extensions import Self
from .models import User, VerificationCode

class BasePhoneValidatorMixin:
    """Миксин для валидации номера телефона"""
    
    def validate_phone_number(self: Self, value: str):
        if not value.startswith('+'):
            raise serializers.ValidationError("Номер телефона должен начинаться с '+'")
        if len(value) < 10:
            raise serializers.ValidationError("Номер телефона слишком короткий")
        return value

class PhoneSerializer(BasePhoneValidatorMixin, serializers.Serializer):
    """Сериализатор для отправки номера телефона"""
    phone_number = serializers.CharField(max_length=15)

class CodeSerializer(BasePhoneValidatorMixin, serializers.Serializer):
    """Сериализатор для верификации кода"""
    phone_number = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=4)
    
    def validate_code(self: Self, value: str):
        if not value:
            raise serializers.ValidationError("Код не может быть пустым")
        return value

class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя"""
    referrals = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 
            'phone_number', 
            'invite_code', 
            'activated_invite_code', 
            'referrals', 
            'created_at'
        ]
        read_only_fields = [
            'id', 
            'invite_code', 
            'activated_invite_code', 
            'referrals', 
            'created_at'
        ]
    
    def get_referrals(self: Self, obj: User):
        """Получает список рефералов пользователя"""
        referrals = User.objects.filter(activated_invite_code=obj.invite_code)
        return [user.phone_number for user in referrals]

class UserAuthSerializer(serializers.ModelSerializer):
    """Сериализатор для аутентификации пользователя"""
    
    class Meta:
        model = User
        fields = [
            'id', 
            'phone_number', 
            'invite_code', 
            'activated_invite_code', 
            'created_at'
        ]
        read_only_fields = [
            'id', 
            'invite_code', 
            'activated_invite_code', 
            'created_at'
        ]

class ActivateInviteSerializer(serializers.Serializer):
    """Сериализатор для активации инвайт-кода"""
    invite_code = serializers.CharField(max_length=6)
    
    def validate_invite_code(self: Self, value: str):
        if not value:
            raise serializers.ValidationError("Инвайт-код не может быть пустым")
        return value 
    
class VerificationCodeResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа при отправке кода верификации"""
    message = serializers.CharField()
    phone_number = serializers.CharField()
    code = serializers.CharField(required=False) 


class ErrorSerializer(serializers.Serializer):
    """
    Сериализатор для стандартизированного формата ошибок
    """
    status = serializers.CharField(help_text="Статус ошибки (например, error)")
    code = serializers.CharField(
        help_text="Код ошибки для программной обработки", 
        required=False
    )
    message = serializers.CharField(
        help_text="Человекочитаемое сообщение об ошибке"
    )
    details = serializers.DictField(
        help_text="Дополнительные детали ошибки", 
        required=False
    )