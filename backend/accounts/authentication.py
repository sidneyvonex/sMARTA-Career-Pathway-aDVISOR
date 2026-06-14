from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError


class CookieJWTAuthentication(JWTAuthentication):
    """
    Reads the JWT access token from an httpOnly cookie instead of the
    Authorization header. Cookie name is configurable via SIMPLE_JWT['AUTH_COOKIE'].
    Returns None only when the cookie is absent (unauthenticated request).
    Raises AuthenticationFailed when a token is present but invalid or expired.
    """

    def authenticate(self, request):
        cookie_name = settings.SIMPLE_JWT.get('AUTH_COOKIE', 'access_token')
        raw_token = request.COOKIES.get(cookie_name)
        if raw_token is None:
            return None
        try:
            validated_token = self.get_validated_token(raw_token)
        except TokenError as e:
            raise AuthenticationFailed(str(e))
        return self.get_user(validated_token), validated_token
