from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        cookie_name = getattr(settings, 'SIMPLE_JWT', {}).get(
            'AUTH_COOKIE', 'owner_access'
        )
        raw_token = request.COOKIES.get(cookie_name)
        if raw_token is None:
            return None
        try:
            validated = self.get_validated_token(raw_token)
            return self.get_user(validated), validated
        except (InvalidToken, TokenError):
            return None
