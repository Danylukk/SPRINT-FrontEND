"""Cadastro acumulativo: preserva o seed das sprints e grava novos ativos em runtime."""
import json
from pathlib import Path

from src.models.equipment import Equipment
from src.repositories.errors import RepositoryDataError


class FleetRepository:
    def __init__(self, data_dir: Path):
        self.seed = data_dir / "equipments.json"
        self.runtime = data_dir / "runtime/equipments.json"

    def _load(self, path, optional=False):
        if optional and not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("Formato inválido")
            return [Equipment.from_dict(item) for item in data]
        except (OSError, ValueError, TypeError, AttributeError) as error:
            raise RepositoryDataError("Não foi possível ler o cadastro; o arquivo foi preservado.") from error

    def get_all(self):
        seed = self._load(self.seed)
        new = self._load(self.runtime, optional=True)
        tags = {item.tag for item in seed}
        return seed + [item for item in new if item.tag not in tags]

    def find_by_tag(self, tag):
        return next((item for item in self.get_all() if item.tag == tag.strip().upper()), None)

    def add(self, equipment):
        items = self._load(self.runtime, optional=True)
        items.append(equipment)
        temporary = self.runtime.with_suffix(".tmp")
        try:
            self.runtime.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(json.dumps([item.to_dict() for item in items], ensure_ascii=False,
                                            indent=2, allow_nan=False), encoding="utf-8")
            temporary.replace(self.runtime)
        except OSError as error:
            raise RepositoryDataError("Não foi possível gravar o cadastro.") from error
