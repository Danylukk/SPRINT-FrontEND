from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.repositories.errors import RepositoryDataError


class TelemetryRepository:
    """Lê o histórico versionado e grava apenas novas leituras em runtime."""

    COLUMNS = [
        "timestamp",
        "tag",
        "temperatura_c",
        "vibracao_mm_s",
        "corrente_a",
        "rotacao_rpm",
        "reading_id",
        "source",
    ]

    def __init__(
        self,
        seed_path: str | Path = "data/telemetry_history.csv",
        runtime_path: str | Path | None = None,
    ) -> None:
        self.seed_path = Path(seed_path)
        self.runtime_path = (
            Path(runtime_path)
            if runtime_path is not None
            else self.seed_path.parent / "runtime" / self.seed_path.name
        )

    def read_history(self) -> pd.DataFrame:
        seed_history = self._read_file(self.seed_path, default_source="seed_history")
        runtime_history = self._read_file(self.runtime_path, default_source="runtime_simulation")
        history = pd.concat([seed_history, runtime_history], ignore_index=True)
        if history.empty:
            return pd.DataFrame(columns=self.COLUMNS)
        return history.sort_values("timestamp").reset_index(drop=True)

    def append_rows(self, rows: list[dict]) -> None:
        if not rows:
            return
        normalized = self._normalize(pd.DataFrame(rows), default_source="runtime_simulation")
        self.runtime_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            normalized.to_csv(
                self.runtime_path,
                index=False,
                mode="a",
                header=not self.runtime_path.exists() or self.runtime_path.stat().st_size == 0,
            )
        except OSError as error:
            raise RepositoryDataError("Não foi possível gravar a telemetria de execução.") from error

    def _read_file(self, path: Path, *, default_source: str) -> pd.DataFrame:
        if not path.exists() or path.stat().st_size == 0:
            return pd.DataFrame(columns=self.COLUMNS)
        try:
            history = pd.read_csv(path)
        except (pd.errors.ParserError, UnicodeDecodeError, OSError) as error:
            raise RepositoryDataError(f"Não foi possível ler a telemetria em {path}.") from error
        return self._normalize(history, default_source=default_source)

    def _normalize(self, history: pd.DataFrame, *, default_source: str) -> pd.DataFrame:
        history = history.copy()
        for column in self.COLUMNS:
            if column not in history.columns:
                history[column] = pd.NA

        history = history[self.COLUMNS]
        history["timestamp"] = pd.to_datetime(history["timestamp"], errors="coerce")
        for column in ["temperatura_c", "vibracao_mm_s", "corrente_a", "rotacao_rpm"]:
            history[column] = pd.to_numeric(history[column], errors="coerce")

        history = history.dropna(subset=["timestamp", "tag"]).copy()
        history["tag"] = history["tag"].astype(str)
        history["source"] = history["source"].fillna(default_source).replace("", default_source).astype(str)
        missing_ids = history["reading_id"].isna() | (history["reading_id"].astype(str).str.strip() == "")
        history.loc[missing_ids, "reading_id"] = history.loc[missing_ids].apply(
            lambda row: f"seed-{row['tag']}-{row['timestamp'].isoformat()}", axis=1
        )
        history["reading_id"] = history["reading_id"].astype(str)
        return history
