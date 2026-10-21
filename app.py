"""Entrada única e compatível com `streamlit run app.py` na raiz."""
import runpy
import sys
from pathlib import Path


def main() -> None:
    frontend = Path(__file__).resolve().parent / "frontend"
    sys.path.insert(0, str(frontend))
    runpy.run_path(str(frontend / "app.py"), run_name="__main__")


if __name__ == "__main__":
    main()
