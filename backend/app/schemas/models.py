from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Credentials(InputModel):
    usuario: str = Field(min_length=3, max_length=40, pattern=r"^[a-zA-Z0-9_.-]+$")
    # Senhas preservam os caracteres digitados, inclusive espaços.
    senha: str = Field(min_length=8, max_length=128)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)


class User(BaseModel):
    id: int
    usuario: str


class LoginResult(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    usuario: User


class ConversationInput(InputModel):
    titulo: str = Field(default="Nova conversa", min_length=1, max_length=80)


class MessageInput(InputModel):
    conteudo: str = Field(min_length=1, max_length=4000)


class Message(BaseModel):
    id: int
    papel: Literal["user", "assistant"]
    conteudo: str
    criado_em: datetime


class Conversation(BaseModel):
    id: int
    titulo: str
    criado_em: datetime
    atualizado_em: datetime


class ConversationDetail(Conversation):
    mensagens: list[Message]


class MessageResult(BaseModel):
    conversa_id: int
    mensagem_usuario: Message
    resposta: Message
    modelo: str
    criado_em: datetime


class Health(BaseModel):
    status: Literal["ok", "degraded"]
    provider: str
    modelo: str


class ErrorResponse(BaseModel):
    detail: str
