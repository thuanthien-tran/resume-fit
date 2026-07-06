from abc import ABC, abstractmethod


class AuthProvider(ABC):
    @abstractmethod
    def verify_access_token(self, token: str) -> dict:
        pass
