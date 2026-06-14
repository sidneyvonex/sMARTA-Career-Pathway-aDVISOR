from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError


class CookieJWTAuthentication(JWTAuthentication):
    """
    Reads the JWT access token from an httpOnly cookie instead of the
    Authorization header. Cookie name is configurable via SIMPLE_JWT['AUTH_COOKIE'].
    Returns None (unauthenticated) rather than raising on missing or invalid tokens,
    so public endpoints still work without a cookie present.
    """

    def authenticate(self, request):
        cookie_name = settings.SIMPLE_JWT.get('AUTH_COOKIE', 'access_token')
        raw_token = request.COOKIES.get(cookie_name)
        if raw_token is None:
            return None
        try:
            validated_token = self.get_validated_token(raw_token)
        except TokenError:
            return None
        return self.get_user(validated_token), validated_token
