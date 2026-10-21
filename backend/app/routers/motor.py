from fastapi import APIRouter, Depends, Request

from app.core.dependencies import current_user
from app.schemas.motor import DemoResult, EquipmentCreate, EquipmentOutput, Panel, RawSensors, Telemetry

router = APIRouter(prefix="/motor", tags=["Motor Digital Twin"], dependencies=[Depends(current_user)])


def motor_service(request: Request):
    return request.app.state.motor_service


@router.get("/equipamentos", response_model=list[EquipmentOutput], summary="Listar o cadastro compartilhado das sprints")
def list_equipments(service=Depends(motor_service)):
    return service.list()


@router.post("/equipamentos", response_model=EquipmentOutput, status_code=201,
             summary="Cadastrar equipamento com confirmação explícita e TAG única")
def create_equipment(data: EquipmentCreate, service=Depends(motor_service)):
    return service.create(data)


@router.get("/painel", response_model=Panel, summary="Consultar estados, alertas e eventos das sprints")
def panel(include_seed: bool = False, service=Depends(motor_service)):
    return service.panel(include_seed)


@router.get("/equipamentos/{tag}", response_model=Telemetry, summary="Abrir ficha, leitura atual e histórico do equipamento")
def detail(tag: str, service=Depends(motor_service)):
    return service.detail(tag)


@router.post("/equipamentos/{tag}/demo", response_model=DemoResult, status_code=201,
             summary="Alternar a DEMO da Sprint 3 e registrar transições reais")
def demo(tag: str, service=Depends(motor_service)):
    return service.refresh(tag, demo=True)


@router.post("/equipamentos/{tag}/leituras", response_model=DemoResult, status_code=201,
             summary="Gerar e persistir uma leitura simulada da Sprint 2")
def reading(tag: str, service=Depends(motor_service)):
    return service.refresh(tag)


@router.get("/equipamentos/{tag}/sensores", response_model=RawSensors,
            summary="Simular dados brutos e converter com as fórmulas da Sprint 1")
def raw(tag: str, service=Depends(motor_service)):
    return service.raw(tag)
