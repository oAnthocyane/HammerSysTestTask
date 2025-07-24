import random
import time
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import User, VerificationCode, CodeGenerationError
from .serializers import (
    PhoneSerializer, 
    CodeSerializer, 
    UserProfileSerializer, 
    UserAuthSerializer, 
    ActivateInviteSerializer,
    VerificationCodeResponseSerializer,
    ErrorSerializer 
)
from .utils import create_error_response

logger = logging.getLogger(__name__)

phone_number_param = openapi.Parameter(
    'phone_number', 
    openapi.IN_QUERY, 
    description="Номер телефона в международном формате", 
    type=openapi.TYPE_STRING
)

send_code_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'phone_number': openapi.Schema(
            type=openapi.TYPE_STRING, 
            description='Номер телефона в международном формате (начинается с +)',
            example='+79991234567'
        )
    },
    required=['phone_number']
)

send_code_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Сообщение о результате'),
        'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Номер телефона'),
        'code': openapi.Schema(type=openapi.TYPE_STRING, description='Код верификации (только для тестирования)')
    }
)

verify_code_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'phone_number': openapi.Schema(
            type=openapi.TYPE_STRING, 
            description='Номер телефона в международном формате',
            example='+79991234567'
        ),
        'code': openapi.Schema(
            type=openapi.TYPE_STRING, 
            description='Код верификации (4 цифры)',
            example='1234'
        )
    },
    required=['phone_number', 'code']
)

activate_invite_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'invite_code': openapi.Schema(
            type=openapi.TYPE_STRING, 
            description='Инвайт-код для активации',
            example='A1B2C3'
        )
    },
    required=['invite_code']
)

@swagger_auto_schema(
    method='post',
    operation_description="Отправка кода верификации на номер телефона",
    request_body=send_code_request,
    responses={
        200: send_code_response,
        400: openapi.Response(description="Ошибка валидации", schema=ErrorSerializer()),
        500: openapi.Response(description="Ошибка сервера", schema=ErrorSerializer())
    }
)
@api_view(['POST'])
def send_code(request):
    """
    Отправка кода верификации на номер телефона
    """
    serializer = PhoneSerializer(data=request.data)
    if serializer.is_valid():
        phone_number = serializer.validated_data['phone_number']
        
        try:
            verification_code = VerificationCode.create_code(phone_number)
            logger.info(f"Создан код верификации {verification_code.code} для номера {phone_number}")
        except CodeGenerationError as e:
            logger.error(f"Ошибка генерации кода для {phone_number}: {str(e)}")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                str(e),
                'CODE_GENERATION_ERROR'
            )
        
        delay = random.uniform(1, 2)
        time.sleep(delay)
        logger.debug(f"Задержка отправки кода: {delay:.2f} секунд")
        
        response_serializer = VerificationCodeResponseSerializer({
            'message': 'Код успешно отправлен',
            'phone_number': phone_number,
            'code': verification_code.code
        })
        return Response(response_serializer.data)
    
    logger.warning(f"Невалидные данные при отправке кода: {serializer.errors}")
    error_details = {}
    for field, errors in serializer.errors.items():
        error_details[field] = errors[0] if isinstance(errors, list) and errors else str(errors)

    return create_error_response(
        status.HTTP_400_BAD_REQUEST,
        'Неверные данные запроса',
        'VALIDATION_ERROR',
        error_details
    )

@swagger_auto_schema(
    method='post',
    operation_description="Верификация кода и создание/аутентификация пользователя",
    request_body=verify_code_request,
    responses={
        200: openapi.Response(
            description="Успешная аутентификация",
            schema=UserAuthSerializer
        ),
        400: openapi.Response(
            description="Ошибка верификации",
            schema=ErrorSerializer()
        ),
        404: openapi.Response(
            description="Код не найден",
            schema=ErrorSerializer()
        ),
        500: openapi.Response(
            description="Ошибка сервера",
            schema=ErrorSerializer()
        )
    }
)
@api_view(['POST'])
def verify_code(request):
    """
    Верификация кода и создание/аутентификация пользователя
    """
    serializer = CodeSerializer(data=request.data)
    if serializer.is_valid():
        phone_number = serializer.validated_data['phone_number']
        code = serializer.validated_data['code']
        
        try:
            verification_code = VerificationCode.objects.get(
                phone_number=phone_number,
                code=code
            )
            
            if not verification_code.is_valid():
                verification_code.delete()
                logger.warning(f"Попытка использования просроченного кода для {phone_number}")
                return create_error_response(
                    status.HTTP_400_BAD_REQUEST,
                    'Код истек',
                    'CODE_EXPIRED'
                )
            
            verification_code.delete()
            logger.info(f"Код верификации успешно использован для {phone_number}")
            
            try:
                user, created = User.objects.get_or_create(phone_number=phone_number)
                if created:
                    logger.info(f"Создан новый пользователь: {phone_number}")
                else:
                    logger.info(f"Аутентификация существующего пользователя: {phone_number}")
            except IntegrityError as e:
                logger.error(f"Ошибка создания пользователя {phone_number}: {str(e)}")
                return create_error_response(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    'Ошибка создания пользователя',
                    'USER_CREATION_ERROR',
                    {'error_details': str(e)}
                )
            
            request.session['user_id'] = user.id
            logger.debug(f"Пользователь {user.id} аутентифицирован, ID сохранен в сессии")
            
            user_serializer = UserAuthSerializer(user)
            response_data = user_serializer.data
            response_data['is_new_user'] = created
            
            return Response(response_data)
            
        except VerificationCode.DoesNotExist:
            logger.warning(f"Попытка использования неверного кода для {phone_number}")
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                'Неверный код',
                'INVALID_CODE'
            )
    
    logger.warning(f"Невалидные данные при верификации кода: {serializer.errors}")
    error_details = {}
    for field, errors in serializer.errors.items():
        error_details[field] = errors[0] if isinstance(errors, list) and errors else str(errors)

    return create_error_response(
        status.HTTP_400_BAD_REQUEST,
        'Неверные данные запроса',
        'VALIDATION_ERROR',
        error_details
    )

@swagger_auto_schema(
    method='get',
    operation_description="Получение профиля пользователя",
    responses={
        200: openapi.Response(
            description="Профиль пользователя",
            schema=UserProfileSerializer
        ),
        401: openapi.Response(
            description="Не авторизован",
            schema=ErrorSerializer()
        ),
        404: openapi.Response(
            description="Пользователь не найден",
            schema=ErrorSerializer()
        )
    }
)
@api_view(['GET'])
def profile(request):
    """
    Получение профиля пользователя
    """
    user_id = request.session.get('user_id')
    if not user_id:
        logger.warning("Попытка доступа к профилю неаутентифицированного пользователя")
        return create_error_response(
            status.HTTP_401_UNAUTHORIZED,
            'Необходима аутентификация',
            'NOT_AUTHENTICATED'
        )
    
    try:
        user = User.objects.get(id=user_id)
        logger.debug(f"Получен профиль пользователя {user_id}")
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)
    except User.DoesNotExist:
        logger.error(f"Пользователь с ID {user_id} не найден")
        return create_error_response(
            status.HTTP_404_NOT_FOUND,
            'Пользователь не найден',
            'USER_NOT_FOUND'
        )

@swagger_auto_schema(
    method='post',
    operation_description="Активация инвайт-кода",
    request_body=activate_invite_request,
    responses={
        200: openapi.Response(
            description="Инвайт-код успешно активирован",
            schema=UserProfileSerializer
        ),
        400: openapi.Response(
            description="Ошибка активации",
            schema=ErrorSerializer()
        ),
        401: openapi.Response(
            description="Не авторизован",
            schema=ErrorSerializer()
        ),
        404: openapi.Response(
            description="Пользователь не найден",
            schema=ErrorSerializer()
        )
    }
)
@api_view(['POST'])
def activate_invite(request):
    """
    Активация инвайт-кода
    """
    user_id = request.session.get('user_id')
    if not user_id:
        logger.warning("Попытка активации инвайт-кода неаутентифицированным пользователем")
        return create_error_response(
            status.HTTP_401_UNAUTHORIZED,
            'Необходима аутентификация',
            'NOT_AUTHENTICATED'
        )
    
    try:
        user = User.objects.get(id=user_id)
        logger.debug(f"Пользователь {user_id} инициировал активацию инвайт-кода")
    except User.DoesNotExist:
        logger.error(f"Пользователь с ID {user_id} не найден при активации инвайт-кода")
        return create_error_response(
            status.HTTP_404_NOT_FOUND,
            'Пользователь не найден',
            'USER_NOT_FOUND'
        )
    
    if user.activated_invite_code:
        logger.warning(f"Пользователь {user_id} пытается активировать второй инвайт-код")
        return create_error_response(
            status.HTTP_400_BAD_REQUEST,
            'Инвайт-код уже активирован',
            'INVITE_ALREADY_ACTIVATED'
        )
    
    serializer = ActivateInviteSerializer(data=request.data)
    if serializer.is_valid():
        invite_code = serializer.validated_data['invite_code']
        
        try:
            invited_user = User.objects.get(invite_code__iexact=invite_code)
        except User.DoesNotExist:
            logger.warning(f"Попытка активации несуществующего инвайт-кода: {invite_code}")
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                'Неверный инвайт-код',
                'INVALID_INVITE_CODE'
            )
        
        if invited_user.id == user.id:
            logger.warning(f"Пользователь {user_id} пытается использовать свой собственный инвайт-код")
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                'Нельзя использовать свой собственный инвайт-код',
                'SELF_INVITE_NOT_ALLOWED'
            )
        
        user.activated_invite_code = invited_user.invite_code 
        user.save()
        logger.info(f"Пользователь {user_id} успешно активировал инвайт-код {invite_code}")
        
        updated_serializer = UserProfileSerializer(user)
        return Response(updated_serializer.data)
    
    logger.warning(f"Невалидные данные при активации инвайт-кода: {serializer.errors}")
    error_details = {}
    for field, errors in serializer.errors.items():
        error_details[field] = errors[0] if isinstance(errors, list) and errors else str(errors)

    return create_error_response(
        status.HTTP_400_BAD_REQUEST,
        'Неверные данные запроса',
        'VALIDATION_ERROR',
        error_details
    )