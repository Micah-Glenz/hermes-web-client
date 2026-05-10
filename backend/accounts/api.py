from ninja import Router
from ninja import Schema
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import AccessToken

router = Router(tags=["auth"])

class LoginIn(Schema):
    username: str
    password: str

class LoginOut(Schema):
    access: str
    token_type: str = "Bearer"

@router.post("/login", auth=None, response=LoginOut)
def login(request, payload: LoginIn):
    user = authenticate(username=payload.username, password=payload.password)
    if not user:
        return 401, {"error": "Invalid credentials"}
    token = AccessToken.for_user(user)
    return {"access": str(token), "token_type": "Bearer"}
