from app.auth.base import AuthProvider
from app.auth.local_jwt import LocalJwtAuthProvider
from app.core.config import settings


def get_auth_provider() -> AuthProvider:
    if settings.auth_provider == "cognito":
        from app.auth.cognito import CognitoAuthProvider

        return CognitoAuthProvider()
    return LocalJwtAuthProvider()
