from ninja import NinjaAPI
from ninja.security import HttpBearer
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken

class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            AccessToken(token)
            return token
        except InvalidToken:
            return None

api = NinjaAPI(
    title="Hermes Web Client API",
    version="0.1.0",
    auth=JWTAuth(),
)

from accounts.api import router as accounts_router
api.add_router("/auth", accounts_router)
