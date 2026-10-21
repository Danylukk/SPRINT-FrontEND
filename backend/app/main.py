import logging
import sqlite3
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# O domínio das sprints permanece em src/ e é importado somente pelo backend.
PROJECT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_DIR))

from app.core.config import Settings
from app.core.errors import AppError
from app.llm.provider import ModelProvider
from app.repositories.auth import AuthRepository
from app.repositories.conversations import ConversationRepository
from app.repositories.database import Database
from app.routers import auth, conversations, health, motor
from app.services.auth import AuthService
from app.services.chat import ChatService
from app.services.motor import MotorService
from src.repositories.errors import RepositoryDataError


def create_app(settings: Settings | None = None):
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(application):
        database = Database(settings.database_path)
        database.initialize()
        application.state.motor_service = MotorService(settings.motor_data_dir or PROJECT_DIR / "data")
        application.state.auth_service = AuthService(AuthRepository(database), settings.token_ttl_seconds)
        application.state.chat_service = ChatService(
            ConversationRepository(database), ModelProvider(settings.llm_provider), application.state.motor_service
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
    application.include_router(motor.router)

    @application.exception_handler(RepositoryDataError)
    async def motor_data_error(request: Request, error: RepositoryDataError):
        return JSONResponse(status_code=503, content={"detail": "Os dados operacionais estão indisponíveis. Os arquivos foram preservados."})

    return application


app = create_app()
