import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    database_path: Path
    token_ttl_seconds: int = 28800
    llm_provider: str = "simulated"
    motor_data_dir: Path | None = None

    def __post_init__(self):
        if self.token_ttl_seconds < 1:
            raise ValueError("TOKEN_TTL_SECONDS deve ser positivo")
        if self.llm_provider not in {"simulated", "echo", "unavailable"}:
            raise ValueError("LLM_PROVIDER deve ser simulated, echo ou unavailable")

    @classmethod
    def from_env(cls):
        load_dotenv(BACKEND_DIR / ".env", override=False)
        path = Path(os.getenv("DATABASE_PATH", "data/chat.sqlite3"))
        return cls(
            database_path=path if path.is_absolute() else BACKEND_DIR / path,
            token_ttl_seconds=int(os.getenv("TOKEN_TTL_SECONDS", "28800")),
            llm_provider=os.getenv("LLM_PROVIDER", "simulated"),
            motor_data_dir=Path(os.environ["MOTOR_DATA_DIR"]).resolve() if os.getenv("MOTOR_DATA_DIR") else None,
        )
