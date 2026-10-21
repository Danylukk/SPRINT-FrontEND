import logging
import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import Settings
from app.core.errors import AppError
from app.llm.provider import ModelProvider
from app.repositories.auth import AuthRepository
from app.repositories.conversations import ConversationRepository
from app.repositories.database import Database
from app.routers import auth, conversations, health
from app.services.auth import AuthService
from app.services.chat import ChatService


def create_app(settings: Settings | None = None):
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(application):
        database = Database(settings.database_path)
        database.initialize()
        application.state.auth_service = AuthService(AuthRepository(database), settings.token_ttl_seconds)
        application.state.chat_service = ChatService(
            ConversationRepository(database), ModelProvider(settings.llm_provider)
        )
        yield

    application = FastAPI(
        title="CP6 · Motor Digital Twin Chat", version="1.0.0", lifespan=lifespan,
        description="Chat acadêmico com bot simulado, autenticação Bearer e histórico SQLite por usuário.",
    )

    @application.exception_handler(AppError)
    async def application_error(request: Request, error: AppError):
        headers = {"WWW-Authenticate": "Bearer"} if error.status_code == 401 else None
        return JSONResponse(status_code=error.status_code, content={"detail": error.detail}, headers=headers)

    @application.exception_handler(sqlite3.Error)
    async def database_error(request: Request, error: sqlite3.Error):
        logging.getLogger(__name__).error("Falha de persistência: %s", type(error).__name__)
        return JSONResponse(status_code=503, content={"detail": "O armazenamento está indisponível. Tente mais tarde."})

    application.include_router(health.router)
    application.include_router(auth.router)
    application.include_router(conversations.router)
    return application


app = create_app()
