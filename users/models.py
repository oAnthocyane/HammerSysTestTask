import random
import string
from django.db import models
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from .exceptions import CodeGenerationError

class User(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    invite_code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    activated_invite_code = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = self.generate_unique_invite_code()
        super().save(*args, **kwargs)

    @classmethod
    def generate_invite_code(cls, length=None, charset=None):
        """Генерирует один invite код с заданными параметрами"""
        if length is None:
            length = settings.INVITE_CODE_SETTINGS['length']
        if charset is None:
            charset = settings.INVITE_CODE_SETTINGS['charset']
        
        return ''.join(random.choices(charset, k=length))

    def generate_unique_invite_code(self):
        """Генерирует уникальный invite код с ограничением попыток"""
        max_attempts = settings.INVITE_CODE_SETTINGS['max_attempts']
        
        for attempt in range(max_attempts):
            code = self.generate_invite_code()
            if not User.objects.filter(invite_code=code).exists():
                return code
        
        raise CodeGenerationError(
            f"Не удалось сгенерировать уникальный invite код за {max_attempts} попыток"
        )
    
    def __str__(self):
        return f"{self.phone_number} ({self.invite_code})"

    class Meta:
        db_table = 'referral_users'


class VerificationCode(models.Model):
    phone_number = models.CharField(max_length=15)
    code = models.CharField(max_length=4, unique=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    @classmethod
    def generate_verification_code(cls, length=None, charset=None, numeric_only=None):
        """Генерирует один verification код с заданными параметрами"""
        if length is None:
            length = settings.VERIFICATION_CODE_SETTINGS['length']
        if charset is None:
            if numeric_only is None:
                numeric_only = settings.VERIFICATION_CODE_SETTINGS['numeric_only']
            charset = settings.VERIFICATION_CODE_SETTINGS['charset'] if numeric_only else (string.digits + string.ascii_letters)
        
        return ''.join(random.choices(charset, k=length))

    @classmethod
    def create_code(cls, phone_number, length=None, charset=None, expiration_minutes=None):
        """Создает код верификации с настройками из settings"""
        cls.objects.filter(phone_number=phone_number).delete()
        
        if expiration_minutes is None:
            expiration_minutes = settings.VERIFICATION_CODE_SETTINGS['expiration_minutes']
        
        expires_at = timezone.now() + timedelta(minutes=expiration_minutes)
        
        max_attempts = settings.VERIFICATION_CODE_SETTINGS['max_attempts']
        code = None
        
        for attempt in range(max_attempts):
            candidate_code = cls.generate_verification_code(length, charset)
            if not cls.objects.filter(code=candidate_code).exists():
                code = candidate_code
                break
        
        if code is None:
            raise CodeGenerationError(
                f"Не удалось сгенерировать уникальный verification код за {max_attempts} попыток"
            )
        
        verification_code = cls.objects.create(
            phone_number=phone_number,
            code=code,
            expires_at=expires_at
        )
        return verification_code
    
    def is_valid(self):
        """Проверяет, действителен ли код"""
        return timezone.now() < self.expires_at
    
    def delete_if_expired(self):
        """Удаляет код, если он истек"""
        if not self.is_valid():
            self.delete()
            return True
        return False
    
    @classmethod
    def cleanup_expired_codes(cls):
        """Удаляет все просроченные коды"""
        expired_codes = cls.objects.filter(expires_at__lt=timezone.now())
        count = expired_codes.count()
        expired_codes.delete()
        return count

    def __str__(self):
        return f"{self.phone_number}: {self.code}"

    class Meta:
        db_table = 'referral_verification_codes'
        indexes = [
            models.Index(fields=['phone_number', 'created_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['code']),
        ]