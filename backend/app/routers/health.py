from fastapi import APIRouter, Depends

from app.core.dependencies import chat_service
from app.schemas.models import Health

router = APIRouter(tags=["Saúde"])


@router.get("/health", response_model=Health, summary="Consultar saúde da API e o provider configurado")
def health(service=Depends(chat_service)):
    return service.health()
