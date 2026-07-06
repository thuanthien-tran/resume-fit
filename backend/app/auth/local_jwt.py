from app.auth.base import AuthProvider
from app.core.security import decode_access_token


class LocalJwtAuthProvider(AuthProvider):
    def verify_access_token(self, token: str) -> dict:
        return decode_access_token(token)
