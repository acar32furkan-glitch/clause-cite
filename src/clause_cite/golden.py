"""Altın set (golden set): çıkarım davranışını sabitleyen regresyon vakaları.

Her vaka kendi belgelerini, anchor'ını ve **beklenen madde kimliklerini** getirir. Karşılaştırma
**iki yönlüdür**: eksik madde de, fazladan (beklenmeyen) madde de hatadır. Böylece "motor bir madde
daha yakaladı" ya da "yanlış alarm üretmeye başladı" durumları sessizce geçemez; CI kırmızıya döner.

Dosya biçimi (``examples/golden/golden.json``):

```json
{"cases": [{"name": "tedarik", "documents": ["docs/tedarik_sozlesmesi.txt"], "anchor": "2026-01-01",
            "expected": {"DOC1-0001": ["OBLIGATION", "MUST"]}, "expect_unresolved": ["DOC1-0006"]}]}
```
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from clause_cite.extract import extract
from clause_cite.text import load_document


class GoldenCase(BaseModel):
    """Tek regresyon vakası."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    documents: tuple[str, ...]
    anchor: str | None = None
    expected: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    expect_unresolved: tuple[str, ...] = ()


class CaseResult(BaseModel):
    """Bir vakanın sonucu: eşleşen/kaçan/fazla çıkan maddeler."""

    model_config = ConfigDict(frozen=True)

    name: str
    passed: bool
    actual: dict[str, tuple[str, ...]]
    missing: dict[str, tuple[str, ...]]
    unexpected: tuple[str, ...]
    unresolved_mismatch: tuple[str, ...]
    mismatches: tuple[str, ...]


class GoldenResult(BaseModel):
    """Altın setin tamamı."""

    model_config = ConfigDict(frozen=True)

    cases: tuple[CaseResult, ...]

    @property
    def passed(self) -> bool:
        """Tüm vakalar beklendiği gibi davrandıysa ``True``."""
        return all(case.passed for case in self.cases)


def load_golden(root: Path) -> list[GoldenCase]:
    """``golden.json`` dosyasını bir klasörden (ya da doğrudan dosyadan) oku."""
    path = root / "golden.json" if root.is_dir() else root
    if not path.exists():
        msg = f"altın set dosyası yok: {path}"
        raise FileNotFoundError(msg)
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("cases"), list):
        msg = f"{path} içinde 'cases' listesi olmalı"
        raise ValueError(msg)
    return [GoldenCase.model_validate(case) for case in raw["cases"]]


def run_case(case: GoldenCase, root: Path) -> CaseResult:
    """Tek bir vakayı çalıştır ve bulunan maddeleri beklentiyle diff'le."""
    base = root if root.is_dir() else root.parent
    documents = tuple(load_document(base / name) for name in case.documents)
    anchor = date.fromisoformat(case.anchor) if case.anchor else None
    result = extract(documents, anchor=anchor)

    actual: dict[str, tuple[str, ...]] = {
        item.id: (item.kind.value.upper(), item.modality.value.upper()) for item in result.items
    }
    expected: dict[str, tuple[str, ...]] = {
        item_id: tuple(value.upper() for value in values) for item_id, values in case.expected.items()
    }

    missing: dict[str, tuple[str, ...]] = {}
    mismatches: list[str] = []
    for item_id, want in expected.items():
        got = actual.get(item_id)
        if got != want:
            missing[item_id] = want
            mismatches.append(f"{item_id}: beklenen {list(want)} ≠ bulunan {list(got) if got else 'yok'}")
    unexpected = tuple(item_id for item_id in actual if item_id not in expected)
    for item_id in unexpected:
        mismatches.append(f"{item_id}: beklentide olmayan madde bulundu {list(actual[item_id])}")

    expected_unresolved = set(case.expect_unresolved)
    actual_unresolved = set(result.unresolved_ids())
    unresolved_mismatch = tuple(sorted(expected_unresolved ^ actual_unresolved))
    for item_id in unresolved_mismatch:
        mismatches.append(f"{item_id}: çözülemeyen madde beklentisi uyuşmuyor")

    return CaseResult(
        name=case.name,
        passed=not mismatches,
        actual=actual,
        missing=missing,
        unexpected=unexpected,
        unresolved_mismatch=unresolved_mismatch,
        mismatches=tuple(mismatches),
    )


def run_golden(root: Path) -> GoldenResult:
    """Altın setteki her vakayı çalıştır."""
    cases = load_golden(root)
    return GoldenResult(cases=tuple(run_case(case, root) for case in cases))


def render_golden_text(result: GoldenResult) -> str:
    """Altın set çalışmasının Türkçe insan okur özeti."""
    lines = ["ALTIN SET (regresyon) SONUCU", ""]
    for case in result.cases:
        mark = "✔" if case.passed else "✘"
        lines.append(f"  {mark} {case.name:<28} madde {len(case.actual)}")
        for mismatch in case.mismatches:
            lines.append(f"      {mismatch}")
    lines.append("")
    passed = sum(1 for case in result.cases if case.passed)
    lines.append(f"SONUÇ: {passed}/{len(result.cases)} vaka beklenen davranışı verdi")
    return "\n".join(lines)
