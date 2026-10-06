"""Altın set: iki yönlü karşılaştırma (eksik ve beklenmeyen madde), çözülemeyen maddeler."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from clause_cite.golden import GoldenCase, load_golden, render_golden_text, run_case, run_golden


def test_ornek_altin_set_gecer(golden_dir: Path) -> None:
    result = run_golden(golden_dir)
    assert result.passed
    assert len(result.cases) == 5


def test_load_golden_eksik_dosya(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="altın set dosyası yok"):
        load_golden(tmp_path)


def test_load_golden_bozuk_yapi(tmp_path: Path) -> None:
    (tmp_path / "golden.json").write_text(json.dumps({"cases": "değil"}), encoding="utf-8")
    with pytest.raises(ValueError, match="cases"):
        load_golden(tmp_path)


def test_load_golden_dogrudan_dosya(golden_dir: Path) -> None:
    cases = load_golden(golden_dir / "golden.json")
    assert cases[0].documents


def test_eksik_madde_yakalanir(tmp_path: Path) -> None:
    (tmp_path / "d.txt").write_text("Satıcı teslim etmelidir.", encoding="utf-8")
    case = GoldenCase(
        name="eksik",
        documents=("d.txt",),
        expected={"DOC1-0001": ("OBLIGATION", "MUST"), "DOC1-9999": ("PROHIBITION", "MUST")},
    )
    result = run_case(case, tmp_path)
    assert not result.passed
    assert "DOC1-9999" in result.missing


def test_yanlis_tur_yakalanir(tmp_path: Path) -> None:
    (tmp_path / "d.txt").write_text("Satıcı teslim etmelidir.", encoding="utf-8")
    case = GoldenCase(name="yanlış", documents=("d.txt",), expected={"DOC1-0001": ("PROHIBITION", "MUST")})
    result = run_case(case, tmp_path)
    assert not result.passed
    assert "DOC1-0001" in result.missing


def test_beklenmeyen_madde_yakalanir(tmp_path: Path) -> None:
    (tmp_path / "d.txt").write_text("Satıcı teslim etmelidir.", encoding="utf-8")
    case = GoldenCase(name="fazla", documents=("d.txt",), expected={})
    result = run_case(case, tmp_path)
    assert not result.passed
    assert result.unexpected == ("DOC1-0001",)


def test_cozulemeyen_madde_uyusmazligi_yakalanir(tmp_path: Path) -> None:
    (tmp_path / "d.txt").write_text("Satıcı 30 gün içinde teslim etmelidir.", encoding="utf-8")
    case = GoldenCase(
        name="unresolved",
        documents=("d.txt",),
        expected={"DOC1-0001": ("OBLIGATION", "MUST")},
        expect_unresolved=(),
    )
    result = run_case(case, tmp_path)
    assert not result.passed
    assert result.unresolved_mismatch == ("DOC1-0001",)


def test_beklentiyle_uyusan_vaka_gecer(tmp_path: Path) -> None:
    (tmp_path / "d.txt").write_text("Satıcı 30 gün içinde teslim etmelidir.", encoding="utf-8")
    case = GoldenCase(
        name="uyumlu",
        documents=("d.txt",),
        expected={"DOC1-0001": ("OBLIGATION", "MUST")},
        expect_unresolved=("DOC1-0001",),
    )
    result = run_case(case, tmp_path)
    assert result.passed
    assert result.mismatches == ()


def test_render_golden_text_ozet(golden_dir: Path) -> None:
    text = render_golden_text(run_golden(golden_dir))
    assert "ALTIN SET" in text
    assert "SONUÇ: 5/5" in text
