from fastapi import APIRouter, Depends, Path

from app.core.dependencies import chat_service, current_user
from app.schemas.models import (
    Conversation, ConversationDetail, ConversationInput, ErrorResponse, MessageInput, MessageResult,
)

router = APIRouter(prefix="/conversas", tags=["Conversas"], responses={
    401: {"model": ErrorResponse}, 404: {"model": ErrorResponse},
})


@router.get("", response_model=list[Conversation], summary="Listar apenas as conversas da sua conta")
def list_conversations(user=Depends(current_user), service=Depends(chat_service)):
    return service.list(user["id"])


@router.post("", response_model=Conversation, status_code=201, summary="Criar uma conversa na sua conta")
def create(data: ConversationInput, user=Depends(current_user), service=Depends(chat_service)):
    return service.create(user["id"], data)


@router.get("/{conversation_id}", response_model=ConversationDetail,
            summary="Retomar uma conversa sua com todo o histórico persistido")
def get(conversation_id: int = Path(gt=0), user=Depends(current_user), service=Depends(chat_service)):
    return service.get(user["id"], conversation_id)


@router.post("/{conversation_id}/mensagens", response_model=MessageResult, status_code=201,
             summary="Enviar texto e persistir a resposta do bot na mesma transação",
             responses={503: {"model": ErrorResponse}})
def send(data: MessageInput, conversation_id: int = Path(gt=0),
         user=Depends(current_user), service=Depends(chat_service)):
    return service.send(user["id"], conversation_id, data)
