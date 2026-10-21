"""Adapta os serviços existentes das Sprints 1–3 para a API, sem duplicar regras."""
import json
import re
from dataclasses import asdict, replace
from math import isfinite
from pathlib import Path
from threading import RLock

from app.core.errors import AppError
from app.repositories.fleet import FleetRepository
from src.repositories.event_repository import EventRepository
from src.repositories.telemetry_repository import TelemetryRepository
from src.services.equipment_service import EquipmentService, EquipmentValidationError
from src.services.operational_intelligence_service import OperationalIntelligenceService
from src.services.sensor_service import build_sensor_table, convert_raw_sensor_data, simulate_raw_sensor_data
from src.services.telemetry_service import TelemetryService


def json_safe(value):
    if isinstance(value, float) and not isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


class MotorService:
    def __init__(self, data_dir: Path):
        self.equipment = EquipmentService(FleetRepository(data_dir))
        self.telemetry = TelemetryService(TelemetryRepository(data_dir / "telemetry_history.csv"))
        self.events = EventRepository(data_dir / "event_history.csv")
        self.intelligence = OperationalIntelligenceService()
        self.snapshots = {}
        # A aplicação local usa um processo Uvicorn. Serializa cadastro, leituras e transições.
        self.lock = RLock()

    def list(self):
        with self.lock:
            return [item.to_dict() for item in self.equipment.list_equipments()]

    def get(self, tag):
        equipment = self.equipment.get_by_tag(tag)
        if equipment is None:
            raise AppError(404, "Equipamento não encontrado.")
        return equipment

    def create(self, data):
        with self.lock:
            try:
                result = self.equipment.create_equipment(data.model_dump(exclude={"confirmar"}),
                                                         confirm_save=data.confirmar)
            except EquipmentValidationError as error:
                raise AppError(409 if "já está cadastrada" in str(error) else 422, str(error)) from error
            return result.to_dict()

    def snapshot(self, equipment):
        reading = self.telemetry.get_current_reading(equipment)
        previous = self.snapshots.get(equipment.tag)
        if previous and previous.reading_id == reading["reading_id"]:
            current = replace(previous, is_stale=self.intelligence._is_stale(previous.timestamp))
        else:
            current = self.intelligence.analyze(equipment, reading)
        self.snapshots[equipment.tag] = current
        return current

    def panel(self, include_seed=False):
        with self.lock:
            equipments = self.equipment.list_equipments()
            self.telemetry.ensure_history(equipments)
            return json_safe({
                "equipamentos": [item.to_dict() for item in equipments],
                "snapshots": [asdict(self.snapshot(item)) for item in equipments],
                "eventos": [event.to_dict() for event in self.events.list_recent(50, include_seed=include_seed)],
            })

    def detail(self, tag):
        with self.lock:
            equipment = self.get(tag)
            snapshot = self.snapshot(equipment)
            history = self.telemetry.prepare_chart_data(equipment)
            return json_safe({"equipamento": equipment.to_dict(), "snapshot": asdict(snapshot),
                              "historico": json.loads(history.to_json(orient="records", date_format="iso"))})

    def _record_transition(self, previous, current):
        event = self.intelligence.build_transition_event(current, previous_status=previous.status)
        if event:
            self.events.append_if_new(event)

    def refresh(self, tag, demo=False):
        with self.lock:
            equipment = self.get(tag)
            previous = self.snapshot(equipment)
            if demo:
                scenario = "baseline" if previous.status == "Crítico" else "critical"
                reading = self.telemetry.append_demo_reading(equipment, scenario=scenario)
            else:
                reading = self.telemetry.append_current_snapshot(equipment)
            current = self.intelligence.analyze(equipment, reading)
            self._record_transition(previous, current)
            self.snapshots[equipment.tag] = current
            return json_safe({"snapshot": asdict(current),
                "mensagem": f"{equipment.tag}: {previous.status} → {current.status}. Nova leitura gravada no backend."})

    def raw(self, tag):
        with self.lock:
            equipment = self.get(tag)
            raw = simulate_raw_sensor_data(equipment)
            converted = convert_raw_sensor_data(raw, equipment)
            rows = build_sensor_table(raw, converted)
            return {"tag": equipment.tag, "tabela": [
                {"sensor": row["Nome do sensor"], "bruto": row["Valor bruto"],
                 "formula": row["Fórmula/conversão aplicada"], "convertido": row["Valor convertido"]}
                for row in rows
            ]}

    def chat_context(self, content):
        candidates = re.findall(r"(?<!\w)[A-Za-z][A-Za-z0-9]*[-_][A-Za-z0-9_-]+(?!\w)", content)
        if not candidates:
            return None
        with self.lock:
            for candidate in candidates:
                equipment = self.equipment.get_by_tag(candidate)
                if equipment:
                    return json_safe({"equipamento": equipment.to_dict(), "snapshot": asdict(self.snapshot(equipment))})
        return None
