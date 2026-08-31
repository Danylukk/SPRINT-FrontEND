from __future__ import annotations

import csv
from pathlib import Path

from src.models.operational_event import OperationalEvent
from src.repositories.errors import RepositoryDataError


class EventRepository:
    """Mantém eventos versionados como referência e grava eventos novos em runtime."""

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
        "reading_id",
        "inference_id",
    ]

    def __init__(
        self,
        seed_path: str | Path = "data/event_history.csv",
        runtime_path: str | Path | None = None,
    ) -> None:
        self.seed_path = Path(seed_path)
        self.runtime_path = (
            Path(runtime_path)
            if runtime_path is not None
            else self.seed_path.parent / "runtime" / self.seed_path.name
        )

    def append_if_new(self, event: OperationalEvent) -> bool:
        if self._event_exists(event):
            return False
        self._append_runtime(event)
        return True

    def list_recent(self, limit: int = 20, *, include_seed: bool = True) -> list[OperationalEvent]:
        paths = [self.runtime_path]
        if include_seed:
            paths.append(self.seed_path)
        events = [event for path in paths for event in self._read_events(path)]
        events.sort(key=lambda event: event.timestamp, reverse=True)
        return events[: max(0, limit)]

    def _event_exists(self, candidate: OperationalEvent) -> bool:
        return any(
            event.reading_id == candidate.reading_id
            and event.inference_id == candidate.inference_id
            for event in self._read_events(self.runtime_path)
        )

    def _append_runtime(self, event: OperationalEvent) -> None:
        self.runtime_path.parent.mkdir(parents=True, exist_ok=True)
        needs_header = not self.runtime_path.exists() or self.runtime_path.stat().st_size == 0
        try:
            with self.runtime_path.open("a", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=self.FIELDNAMES)
                if needs_header:
                    writer.writeheader()
                writer.writerow(event.to_dict())
        except OSError as error:
            raise RepositoryDataError("Não foi possível gravar o histórico de eventos.") from error

    def _read_events(self, path: Path) -> list[OperationalEvent]:
        if not path.exists() or path.stat().st_size == 0:
            return []
        try:
            with path.open("r", newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file, strict=True))
        except (csv.Error, OSError, UnicodeDecodeError) as error:
            raise RepositoryDataError(f"Não foi possível ler o histórico de eventos em {path}.") from error
        return [OperationalEvent.from_dict(row) for row in rows]
