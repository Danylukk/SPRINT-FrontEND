from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class OperationalEvent:
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
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OperationalEvent":
        return cls(
            id=str(data.get("id") or uuid4()),
            timestamp=str(data.get("timestamp") or datetime.now().isoformat(timespec="seconds")),
            tag=str(data.get("tag", "")),
            area=str(data.get("area", "")),
            severity=str(data.get("severity", "Informativo")),
            event_type=str(data.get("event_type", "Atualização")),
            metric=str(data.get("metric", "")),
            measured_value=str(data.get("measured_value", "")),
            status_before=str(data.get("status_before", "")),
            status_after=str(data.get("status_after", "")),
            summary=str(data.get("summary", "")),
            recommendation=str(data.get("recommendation", "")),
            source=str(data.get("source", "rules_fallback")),
        )
