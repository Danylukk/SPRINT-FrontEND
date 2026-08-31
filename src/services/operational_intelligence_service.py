from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

from src.models.equipment import Equipment
from src.models.operational_event import OperationalEvent
from src.services.analytics_provider import AnalyticsProvider, RulesAnalyticsProvider
from src.services.nlp_summary_service import NLPSummaryService

STALE_DATA_THRESHOLD_MINUTES = 120


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
    analytics_provider: str
    nlp_provider: str
    score: float | None
    timestamp: str
    reading_id: str
    inference_id: str
    is_stale: bool
    reading: dict[str, Any]


class OperationalIntelligenceService:
    """Camada desacoplada entre o front-end e o processamento analítico.

    A interface consome somente OperationalSnapshot. Hoje o provider é baseado em
    regras; um futuro provider de ML pode manter o mesmo contrato sem alterar a UI.
    """

    def __init__(
        self,
        analytics_provider: AnalyticsProvider | None = None,
        nlp_service: NLPSummaryService | None = None,
        stale_data_threshold_minutes: int = STALE_DATA_THRESHOLD_MINUTES,
    ) -> None:
        self.analytics_provider = analytics_provider or RulesAnalyticsProvider()
        self.nlp_service = nlp_service or NLPSummaryService()
        self.stale_data_threshold_minutes = stale_data_threshold_minutes

    def analyze(
        self,
        equipment: Equipment,
        reading: dict[str, Any],
    ) -> OperationalSnapshot:
        effective_reading = dict(reading)
        assessment = self.analytics_provider.analyze(equipment, effective_reading)
        timestamp = str(effective_reading.get("timestamp") or datetime.now().isoformat(timespec="seconds"))
        reading_id = str(effective_reading.get("reading_id") or uuid4())
        summary = self.nlp_service.build_summary(
            tag=equipment.tag,
            status=assessment.status,
            dominant_metric=assessment.dominant_metric,
            message=assessment.message,
        )
        recommendation = self.nlp_service.build_recommendation(
            status=assessment.status,
            dominant_metric=assessment.dominant_metric,
        )

        return OperationalSnapshot(
            tag=equipment.tag,
            area=equipment.local_instalacao,
            status=assessment.status,
            severity=assessment.severity,
            dominant_metric=assessment.dominant_metric,
            dominant_value=assessment.dominant_value,
            summary=summary,
            recommendation=recommendation,
            source=str(effective_reading.get("source", "seed_history")),
            analytics_provider=assessment.provider,
            nlp_provider=self.nlp_service.provider,
            score=assessment.score,
            timestamp=timestamp,
            reading_id=reading_id,
            inference_id=str(uuid4()),
            is_stale=self._is_stale(timestamp),
            reading=effective_reading,
        )

    def build_transition_event(
        self,
        snapshot: OperationalSnapshot,
        *,
        previous_status: str,
    ) -> OperationalEvent | None:
        """Cria evento somente quando o estado analítico realmente mudou."""
        if previous_status == snapshot.status:
            return None
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
            reading_id=snapshot.reading_id,
            inference_id=snapshot.inference_id,
            timestamp=snapshot.timestamp,
        )

    def _is_stale(self, timestamp: str) -> bool:
        try:
            reading_time = datetime.fromisoformat(timestamp)
        except ValueError:
            return True
        return (datetime.now() - reading_time).total_seconds() > self.stale_data_threshold_minutes * 60
