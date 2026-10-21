from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.models import InputModel


class EquipmentInput(InputModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)
    tag: str = Field(min_length=1, max_length=40, pattern=r"^[a-zA-Z0-9_-]+$")
    modelo: str = Field(min_length=1, max_length=120)
    fabricante: str = Field(min_length=1, max_length=120)
    potencia: float = Field(gt=0)
    unidade_potencia: Literal["kW", "CV"]
    tensao: float = Field(gt=0)
    corrente_nominal: float = Field(gt=0)
    rotacao_nominal: float = Field(gt=0)
    local_instalacao: str = Field(min_length=1, max_length=120)
    status_operacional: Literal["Operacional", "Atenção", "Crítico", "Inativo"]
    observacoes: str = Field(min_length=1, max_length=4000)


class EquipmentCreate(EquipmentInput):
    confirmar: bool = False


class EquipmentOutput(EquipmentInput):
    id: str
    data_cadastro: str


class Reading(BaseModel):
    timestamp: str
    tag: str
    temperatura_c: float | None
    vibracao_mm_s: float | None
    corrente_a: float | None
    rotacao_rpm: float | None
    reading_id: str
    source: str


class Snapshot(BaseModel):
    tag: str
    area: str
    status: str
    severity: str
    dominant_metric: str
    dominant_value: str
    summary: str
    recommendation: str
    source: str
    analytics_provider: str
    nlp_provider: str
    score: float | None
    timestamp: str
    reading_id: str
    inference_id: str
    is_stale: bool
    reading: Reading


class Event(BaseModel):
    id: str
    timestamp: str
    tag: str
    area: str
    severity: str
    event_type: str
    metric: str
    measured_value: str
    status_before: str
    status_after: str
    summary: str
    recommendation: str
    source: str
    reading_id: str
    inference_id: str


class Panel(BaseModel):
    equipamentos: list[EquipmentOutput]
    snapshots: list[Snapshot]
    eventos: list[Event]


class Telemetry(BaseModel):
    equipamento: EquipmentOutput
    snapshot: Snapshot
    historico: list[Reading]


class RawSensorRow(BaseModel):
    sensor: str
    bruto: str
    formula: str
    convertido: str


class RawSensors(BaseModel):
    tag: str
    origem: str = "Simulação acadêmica de ADC; sem sensores reais"
    tabela: list[RawSensorRow]


class DemoResult(BaseModel):
    snapshot: Snapshot
    mensagem: str
