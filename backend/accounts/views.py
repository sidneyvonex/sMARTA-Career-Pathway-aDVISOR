import logging

logger = logging.getLogger(__name__)

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)

from .emails import send_verification_email, send_password_reset_email, send_staff_invite_email, send_parent_invite_email
from .permissions import IsStudent, IsSystemAdmin
from .serializers import StudentRegistrationSerializer, UserSerializer
from .tokens import (
    load_email_verify_token, make_password_reset_token, load_password_reset_token,
    make_invite_token, load_invite_token,
    make_parent_invite_token, load_parent_invite_token,
    TokenExpiredError, TokenInvalidError,
)
from .response import _success, _error
from parents.models import ParentStudentLink


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='10/h', method='POST', block=True))
    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'data': None, 'error': True, 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = serializer.save()
        send_verification_email.delay(user.id, user.email, user.first_name)
        return _success(
            message='Registration successful. Check your email to verify your account.',
            status_code=status.HTTP_201_CREATED,
        )


def _set_auth_cookies(response, access_token: str, refresh_token: str):
    jwt_settings = settings.SIMPLE_JWT
    secure = jwt_settings.get('AUTH_COOKIE_SECURE', True)
    samesite = jwt_settings.get('AUTH_COOKIE_SAMESITE', 'Lax')
    response.set_cookie(
        key=jwt_settings.get('AUTH_COOKIE', 'access_token'),
        value=access_token,
        max_age=int(jwt_settings['ACCESS_TOKEN_LIFETIME'].total_seconds()),
        httponly=True,
        secure=secure,
        samesite=samesite,
    )
    response.set_cookie(
        key=jwt_settings.get('AUTH_COOKIE_REFRESH', 'refresh_token'),
        value=refresh_token,
        max_age=int(jwt_settings['REFRESH_TOKEN_LIFETIME'].total_seconds()),
        httponly=True,
        secure=secure,
        samesite=samesite,
        path='/api/v1/auth/token/refresh/',
    )


def _clear_auth_cookies(response):
    samesite = settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax')
    response.delete_cookie('access_token', samesite=samesite)
    response.delete_cookie('refresh_token', path='/api/v1/auth/token/refresh/', samesite=samesite)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='5/15m', method='POST', block=True))
    def post(self, request):
        email = request.data.get('email', '').lower().strip()
        password = request.data.get('password', '')
        user = authenticate(request, username=email, password=password)
        if user is None:
            return _error('Invalid email or password.', status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        response = _success(
            data={'user': UserSerializer(user).data},
            message='Login successful.',
        )
        _set_auth_cookies(response, str(refresh.access_token), str(refresh))
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get(
            settings.SIMPLE_JWT.get('AUTH_COOKIE_REFRESH', 'refresh_token')
        )
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass
            except Exception:
                logger.exception('Unexpected error during token blacklisting on logout')
        response = _success(message='Logged out successfully.')
        _clear_auth_cookies(response)
        return response


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_cookie = request.COOKIES.get(
            settings.SIMPLE_JWT.get('AUTH_COOKIE_REFRESH', 'refresh_token')
        )
        if not refresh_cookie:
            return _error('Refresh token not found.', status.HTTP_401_UNAUTHORIZED)
        serializer = TokenRefreshSerializer(data={'refresh': refresh_cookie})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            return _error(str(e), status.HTTP_401_UNAUTHORIZED)
        except Exception:
            return _error('Invalid or expired refresh token.', status.HTTP_401_UNAUTHORIZED)
        response = _success(message='Token refreshed.')
        _set_auth_cookies(
            response,
            access_token=serializer.validated_data['access'],
            refresh_token=serializer.validated_data.get('refresh', refresh_cookie),
        )
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return _success(data={'user': UserSerializer(request.user).data})


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.query_params.get('token', '')
        User = get_user_model()
        try:
            payload = load_email_verify_token(token)
            user = User.objects.get(pk=payload['user_id'])
            user.is_email_verified = True
            user.save(update_fields=['is_email_verified'])
            return _success(message='Email verified successfully.')
        except (TokenExpiredError, TokenInvalidError):
            return _error('Invalid or expired verification link.')
        except User.DoesNotExist:
            return _error('User not found.')


class ResendVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='user', rate='3/h', method='POST', block=True))
    def post(self, request):
        if request.user.is_email_verified:
            return _error('Email is already verified.')
        send_verification_email.delay(
            request.user.id, request.user.email, request.user.first_name
        )
        return _success(message='Verification email sent.')


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='5/h', method='POST', block=True))
    def post(self, request):
        email = request.data.get('email', '').lower().strip()
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            send_password_reset_email.delay(user.id, user.email, user.first_name)
        except User.DoesNotExist:
            pass  # Always return 200 — don't reveal whether email exists
        return _success(
            message='If an account with that email exists, a reset link has been sent.'
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token', '')
        password = request.data.get('password', '')
        if not password:
            return _error('Password is required.')
        User = get_user_model()
        try:
            payload = load_password_reset_token(token)
            user = User.objects.get(pk=payload['user_id'])
        except (TokenExpiredError, TokenInvalidError):
            return _error('Invalid or expired reset link.')
        except User.DoesNotExist:
            return _error('User not found.')
        try:
            validate_password(password, user)
        except DjangoValidationError as e:
            return _error(e.messages, status.HTTP_400_BAD_REQUEST)
        user.set_password(password)
        user.save(update_fields=['password'])
        return _success(message='Password reset successfully.')


class InviteStaffView(APIView):
    permission_classes = [IsAuthenticated, IsSystemAdmin]

    def post(self, request):
        email = request.data.get('email', '').lower().strip()
        role = request.data.get('role', '')
        if not email:
            return _error('Email is required.')
        if role not in ('counselor', 'school_admin'):
            return _error('Role must be counselor or school_admin.')
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            return _error('An account with this email already exists.')
        send_staff_invite_email.delay(invitee_email=email, role=role)
        return _success(message=f'Invite sent to {email}.')


class InviteParentView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request):
        parent_email = request.data.get('parent_email', '').lower().strip()
        if not parent_email:
            return _error('Parent email is required.')
        student = request.user
        student_name = f'{student.first_name} {student.last_name}'.strip() or student.email
        send_parent_invite_email.delay(
            student_id=student.id,
            parent_email=parent_email,
            student_name=student_name,
        )
        return _success(message=f'Invite sent to {parent_email}.')


class AcceptInviteView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token', '')
        password = request.data.get('password', '')
        first_name = request.data.get('first_name', '').strip()
        last_name = request.data.get('last_name', '').strip()
        county = request.data.get('county', '')

        if not password:
            return _error('Password is required.')
        if not first_name:
            return _error('First name is required.')
        if not last_name:
            return _error('Last name is required.')

        User = get_user_model()

        # Try staff invite token first; fall back to parent invite token.
        # The token's cryptographic salt determines type — no client input needed.
        try:
            payload = load_invite_token(token)
            email = payload['email']
            role = payload['role']
            student_id = None
        except (TokenExpiredError, TokenInvalidError):
            try:
                payload = load_parent_invite_token(token)
                email = payload['email']
                student_id = payload['student_id']
                role = 'parent'
            except (TokenExpiredError, TokenInvalidError):
                return _error('Invalid or expired invite link.')

        if User.objects.filter(email=email).exists():
            return _error('An account with this email already exists.')

        try:
            validate_password(password)
        except DjangoValidationError as e:
            return _error(e.messages)

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            county=county or None,
            is_email_verified=True,
        )

        link_created = False
        if student_id is not None:
            try:
                student = User.objects.get(pk=student_id, role='student')
                ParentStudentLink.objects.create(parent=user, student=student)
                link_created = True
            except User.DoesNotExist:
                logger.warning(
                    'Parent invite accepted but student_id=%s not found or wrong role',
                    student_id,
                )

        if student_id and not link_created:
            message = 'Account created, but the student could not be found. Contact your school to link your child.'
        else:
            message = 'Account created successfully.'

        refresh = RefreshToken.for_user(user)
        response = _success(
            data={'user': UserSerializer(user).data},
            message=message,
            status_code=status.HTTP_201_CREATED,
        )
        _set_auth_cookies(response, str(refresh.access_token), str(refresh))
        return response
