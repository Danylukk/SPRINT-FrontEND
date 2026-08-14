import csv
from pathlib import Path

from src.models.operational_event import OperationalEvent


class EventRepository:
    FIELDNAMES = [
        "id",
        "timestamp",
        "tag",
        "area",
        "severity",
        "event_type",
        "metric",
        "measured_value",
        "status_before",
        "status_after",
        "summary",
        "recommendation",
        "source",
    ]

    def __init__(self, file_path: str | Path = "data/event_history.csv") -> None:
        self.file_path = Path(file_path)

    def append(self, event: OperationalEvent) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        needs_header = not self.file_path.exists() or self.file_path.stat().st_size == 0
        with self.file_path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self.FIELDNAMES)
            if needs_header:
                writer.writeheader()
            writer.writerow(event.to_dict())

    def list_recent(self, limit: int = 20) -> list[OperationalEvent]:
        if not self.file_path.exists() or self.file_path.stat().st_size == 0:
            return []
        with self.file_path.open("r", newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        events = [OperationalEvent.from_dict(row) for row in rows]
        events.sort(key=lambda event: event.timestamp, reverse=True)
        return events[: max(0, limit)]
