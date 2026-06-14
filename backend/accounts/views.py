from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .emails import send_verification_email
from .serializers import StudentRegistrationSerializer, UserSerializer


def _success(data=None, message='', status_code=status.HTTP_200_OK):
    return Response({'data': data, 'error': None, 'message': message}, status=status_code)


def _error(message, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({'data': None, 'error': True, 'message': message}, status=status_code)


class RegisterView(APIView):
    permission_classes = [AllowAny]

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
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token', path='/api/v1/auth/token/refresh/')


class LoginView(APIView):
    permission_classes = [AllowAny]

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
            except Exception:
                pass
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
        try:
            refresh = RefreshToken(refresh_cookie)
            access_token = str(refresh.access_token)
            new_refresh = str(refresh)
        except Exception:
            return _error('Invalid or expired refresh token.', status.HTTP_401_UNAUTHORIZED)
        response = _success(message='Token refreshed.')
        _set_auth_cookies(response, access_token, new_refresh)
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return _success(data={'user': UserSerializer(request.user).data})
