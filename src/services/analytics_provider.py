from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Protocol

from src.models.equipment import Equipment
from src.services.alert_service import (
    STATUS_UNAVAILABLE,
    AlertResult,
    AlertService,
)


@dataclass(frozen=True)
class AnalyticsAssessment:
    """Resultado técnico da análise, independente da interface Streamlit."""

    status: str
    severity: str
    dominant_metric: str
    dominant_value: str
    message: str
    provider: str
    score: float | None = None


class AnalyticsProvider(Protocol):
    """Contrato que um futuro provider de ML poderá implementar."""

    def analyze(self, equipment: Equipment, reading: dict) -> AnalyticsAssessment: ...


class RulesAnalyticsProvider:
    """Provider determinístico atual; não representa um modelo de Machine Learning."""

    provider_name = "rules_analytics"

    def __init__(self, alert_service: AlertService | None = None) -> None:
        self.alert_service = alert_service or AlertService()

    def analyze(self, equipment: Equipment, reading: dict) -> AnalyticsAssessment:
        results = self.alert_service.evaluate_all(reading, equipment.corrente_nominal)
        status = str(results["geral"])
        metric, alert, value = self._dominant_alert(results, reading)
        return AnalyticsAssessment(
            status=status,
            severity=self._severity_for_status(status),
            dominant_metric=metric,
            dominant_value=value,
            message=alert.message,
            provider=self.provider_name,
        )

    def _dominant_alert(
        self,
        results: dict[str, AlertResult | str],
        reading: dict,
    ) -> tuple[str, AlertResult, str]:
        candidates = [
            ("Temperatura", results["temperatura"], reading.get("temperatura_c"), "°C", 1),
            ("Vibração", results["vibracao"], reading.get("vibracao_mm_s"), "mm/s", 2),
            ("Corrente", results["corrente"], reading.get("corrente_a"), "A", 2),
        ]
        unavailable = next(
            (candidate for candidate in candidates if candidate[1].status == STATUS_UNAVAILABLE),
            None,
        )
        metric, alert, value, unit, decimals = unavailable or max(
            candidates,
            key=lambda item: self.alert_service.STATUS_ORDER[item[1].status],
        )
        return metric, alert, self._format_value(value, unit, decimals)

    @staticmethod
    def _format_value(value: object, unit: str, decimals: int) -> str:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return "Indisponível"
        if not isfinite(numeric_value):
            return "Indisponível"
        return f"{numeric_value:.{decimals}f} {unit}"

    @staticmethod
    def _severity_for_status(status: str) -> str:
        severity = {
            "Crítico": "Alta",
            "Atenção": "Média",
            "Saudável": "Baixa",
            STATUS_UNAVAILABLE: "Informativa",
        }
        return severity.get(status, "Informativa")
