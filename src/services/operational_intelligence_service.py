from dataclasses import dataclass
from typing import Any

from src.models.equipment import Equipment
from src.models.operational_event import OperationalEvent
from src.services.alert_service import (
    STATUS_CRITICAL,
    STATUS_HEALTHY,
    STATUS_WARNING,
    AlertResult,
    AlertService,
)
from src.services.nlp_summary_service import NLPSummaryService


@dataclass(frozen=True)
class OperationalSnapshot:
    tag: str
    area: str
    status: str
    severity: str
    dominant_metric: str
    dominant_value: str
    summary: str
    recommendation: str
    source: str
    nlp_provider: str
    reading: dict[str, Any]


class OperationalIntelligenceService:
    """Camada desacoplada entre o front-end e o processamento analítico.

    Nesta Sprint, AlertService funciona como fallback analítico por regras e o modo
    de demonstração injeta uma leitura controlada. Um modelo de ML futuro pode
    substituir a origem das leituras/alertas mantendo o contrato OperationalSnapshot.
    """

    def __init__(
        self,
        alert_service: AlertService | None = None,
        nlp_service: NLPSummaryService | None = None,
    ) -> None:
        self.alert_service = alert_service or AlertService()
        self.nlp_service = nlp_service or NLPSummaryService()

    def analyze(
        self,
        equipment: Equipment,
        reading: dict[str, Any],
        *,
        simulate_anomaly: bool = False,
    ) -> OperationalSnapshot:
        effective_reading = dict(reading)
        source = "rules_fallback"
        if simulate_anomaly:
            effective_reading = self._build_demo_anomaly(equipment, effective_reading)
            source = "simulation"

        results = self.alert_service.evaluate_all(effective_reading, equipment.corrente_nominal)
        status = str(results["geral"])
        dominant_metric, dominant_alert, dominant_value = self._dominant_alert(results, effective_reading)
        severity = self._severity_for_status(status)
        summary = self.nlp_service.build_summary(
            tag=equipment.tag,
            status=status,
            dominant_metric=dominant_metric,
            message=dominant_alert.message,
        )
        recommendation = self.nlp_service.build_recommendation(
            status=status,
            dominant_metric=dominant_metric,
        )

        return OperationalSnapshot(
            tag=equipment.tag,
            area=equipment.local_instalacao,
            status=status,
            severity=severity,
            dominant_metric=dominant_metric,
            dominant_value=dominant_value,
            summary=summary,
            recommendation=recommendation,
            source=source,
            nlp_provider=self.nlp_service.provider,
            reading=effective_reading,
        )

    def build_transition_event(
        self,
        snapshot: OperationalSnapshot,
        *,
        previous_status: str,
    ) -> OperationalEvent:
        return OperationalEvent(
            tag=snapshot.tag,
            area=snapshot.area,
            severity=snapshot.severity,
            event_type="Mudança de estado operacional",
            metric=snapshot.dominant_metric,
            measured_value=snapshot.dominant_value,
            status_before=previous_status,
            status_after=snapshot.status,
            summary=snapshot.summary,
            recommendation=snapshot.recommendation,
            source=snapshot.source,
        )

    @staticmethod
    def _build_demo_anomaly(equipment: Equipment, reading: dict[str, Any]) -> dict[str, Any]:
        # Cenário controlado: vibração acima do limite crítico já adotado na Sprint 2.
        reading["vibracao_mm_s"] = 7.8
        # Mantém as demais variáveis plausíveis e sem forçar outro gatilho crítico.
        reading["temperatura_c"] = min(float(reading.get("temperatura_c", 65.0)), 78.0)
        if equipment.corrente_nominal > 0:
            reading["corrente_a"] = min(
                float(reading.get("corrente_a", equipment.corrente_nominal)),
                equipment.corrente_nominal * 1.08,
            )
        return reading

    def _dominant_alert(
        self,
        results: dict[str, AlertResult | str],
        reading: dict[str, Any],
    ) -> tuple[str, AlertResult, str]:
        candidates = [
            ("Temperatura", results["temperatura"], f"{float(reading['temperatura_c']):.1f} °C"),
            ("Vibração", results["vibracao"], f"{float(reading['vibracao_mm_s']):.2f} mm/s"),
            ("Corrente", results["corrente"], f"{float(reading['corrente_a']):.2f} A"),
        ]
        metric, alert, value = max(
            candidates,
            key=lambda item: self.alert_service.STATUS_ORDER[item[1].status],
        )
        return metric, alert, value

    @staticmethod
    def _severity_for_status(status: str) -> str:
        if status == STATUS_CRITICAL:
            return "Alta"
        if status == STATUS_WARNING:
            return "Média"
        if status == STATUS_HEALTHY:
            return "Baixa"
        return "Informativa"
