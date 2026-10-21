import secrets
import time

from app.core.errors import AppError
from app.core.security import hash_password, token_digest, verify_password


class AuthService:
    def __init__(self, repository, ttl):
        self.repository = repository
        self.ttl = ttl
        self.dummy_hash = hash_password(secrets.token_urlsafe(24))

    def register(self, credentials):
        result = self.repository.create_user(
            credentials.usuario.lower(), hash_password(credentials.senha)
        )
        if not result:
            raise AppError(409, "Esse nome de usuário já está em uso.")
        return result

    def login(self, credentials):
        user = self.repository.find_user(credentials.usuario)
        valid = verify_password(credentials.senha, user["password_hash"] if user else self.dummy_hash)
        if not user or not valid:
            raise AppError(401, "Usuário ou senha inválidos.")
        token = secrets.token_urlsafe(32)
        self.repository.create_session(token_digest(token), user["id"], time.time() + self.ttl)
        return {"access_token": token, "expires_in": self.ttl,
                "usuario": {"id": user["id"], "usuario": user["username"]}}

    def authenticate(self, token):
        user = self.repository.find_session(token_digest(token), time.time())
        if not user:
            raise AppError(401, "Sessão inválida ou expirada. Entre novamente.")
        return user

    def logout(self, token):
        self.repository.delete_session(token_digest(token))
