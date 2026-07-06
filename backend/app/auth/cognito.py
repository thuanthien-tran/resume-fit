from app.auth.base import AuthProvider


class CognitoAuthProvider(AuthProvider):
    def verify_access_token(self, token: str) -> dict:
        raise NotImplementedError("Cognito auth provider is a deployment-time integration.")
