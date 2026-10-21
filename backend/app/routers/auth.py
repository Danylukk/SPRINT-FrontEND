from fastapi import APIRouter, Depends, Response
from fastapi.security import HTTPAuthorizationCredentials

from app.core.dependencies import auth_service, bearer, current_user
from app.schemas.models import Credentials, ErrorResponse, LoginResult, User

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/register", response_model=User, status_code=201,
             summary="Criar uma conta local com senha protegida por hash",
             responses={409: {"model": ErrorResponse}})
def register(data: Credentials, service=Depends(auth_service)):
    return service.register(data)


@router.post("/login", response_model=LoginResult, summary="Entrar e obter um token Bearer",
             responses={401: {"model": ErrorResponse}})
def login(data: Credentials, service=Depends(auth_service)):
    return service.login(data)


@router.post("/logout", status_code=204, summary="Revogar o token da sessão atual",
             responses={401: {"model": ErrorResponse}})
def logout(user=Depends(current_user), credentials: HTTPAuthorizationCredentials = Depends(bearer),
           service=Depends(auth_service)):
    service.logout(credentials.credentials)
    return Response(status_code=204)


@router.get("/me", response_model=User, summary="Consultar a identidade do token autenticado",
            responses={401: {"model": ErrorResponse}})
def me(user=Depends(current_user)):
    return user
