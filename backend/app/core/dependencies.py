from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import AppError

bearer = HTTPBearer(auto_error=False)


def auth_service(request: Request):
    return request.app.state.auth_service


def chat_service(request: Request):
    return request.app.state.chat_service


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    service=Depends(auth_service),
):
    if not credentials:
        raise AppError(401, "Entre na sua conta para continuar.")
    return service.authenticate(credentials.credentials)
