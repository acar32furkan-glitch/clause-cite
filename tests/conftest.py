"""Ortak pytest fixture'ları ve örnek dizin yolları."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "examples"
DATA_DIR = EXAMPLES / "data"
GOLDEN_DIR = EXAMPLES / "golden"


@pytest.fixture(scope="session")
def data_dir() -> Path:
    """``examples/data`` klasörü."""
    return DATA_DIR


@pytest.fixture(scope="session")
def golden_dir() -> Path:
    """``examples/golden`` klasörü."""
    return GOLDEN_DIR


@pytest.fixture(scope="session")
def tedarik_path() -> Path:
    """Türkçe tedarik sözleşmesi örneği."""
    return DATA_DIR / "tedarik_sozlesmesi.txt"


@pytest.fixture(scope="session")
def supply_path() -> Path:
    """İngilizce tedarik sözleşmesi örneği."""
    return DATA_DIR / "supply_agreement.txt"


@pytest.fixture
def document_file(tmp_path: Path) -> Callable[..., Path]:
    """Geçici bir belge yaz ve yolunu döndür."""

    def _write(text: str, name: str = "belge.txt") -> Path:
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        return path

    return _write
