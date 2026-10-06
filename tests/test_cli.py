"""CLI sözleşmesi: çıkış kodları, JSON/CSV/rapor çıktıları, iş özeti ve bayraklar."""

from __future__ import annotations

import csv
import importlib
import io
import json
from collections.abc import Callable
from pathlib import Path

import pytest

from clause_cite.cli import main
from clause_cite.verify import CitationStats


def test_extract_cikis_kodu_sifir(supply_path: Path) -> None:
    assert main(["extract", str(supply_path), "--anchor", "2026-01-01"]) == 0


def test_extract_json_sozlesmesi(capsys: pytest.CaptureFixture[str], tedarik_path: Path) -> None:
    code = main(["extract", str(tedarik_path), "--anchor", "2026-01-01", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert set(payload) >= {"version", "anchor", "documents", "item_count", "unresolved", "items", "coverage"}
    assert payload["item_count"] == 19
    assert payload["anchor"] == "2026-01-01"
    assert payload["coverage"] == 1.0


def test_extract_report_dosyasi(tmp_path: Path, tedarik_path: Path) -> None:
    target = tmp_path / "out" / "report.json"
    main(["extract", str(tedarik_path), "--report", str(target), "--anchor", "2026-01-01"])
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["item_count"] == 19


def test_extract_csv_dosyasi(tmp_path: Path, tedarik_path: Path) -> None:
    target = tmp_path / "items.csv"
    main(["extract", str(tedarik_path), "--csv", str(target)])
    rows = list(csv.reader(io.StringIO(target.read_text(encoding="utf-8"))))
    assert rows[0][0] == "id"
    assert len(rows) == 20


def test_extract_fail_on_unresolved(capsys: pytest.CaptureFixture[str], tedarik_path: Path) -> None:
    code = main(["extract", str(tedarik_path), "--fail-on-unresolved"])
    assert code == 1
    assert "çözülemedi" in capsys.readouterr().err


def test_extract_anchor_ile_unresolved_kalmaz(tedarik_path: Path) -> None:
    assert main(["extract", str(tedarik_path), "--anchor", "2026-01-01", "--fail-on-unresolved"]) == 0


def test_extract_github_ozeti(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, supply_path: Path) -> None:
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    main(["extract", str(supply_path), "--github-summary"])
    text = summary.read_text(encoding="utf-8")
    assert "### Kanıtlı aksiyon maddeleri" in text


def test_extract_github_ozeti_ortam_yoksa_uyari(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], supply_path: Path
) -> None:
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    main(["extract", str(supply_path), "--github-summary"])
    assert "GITHUB_STEP_SUMMARY tanımlı değil" in capsys.readouterr().err


def test_extract_strict_eleme_raporu(capsys: pytest.CaptureFixture[str], tedarik_path: Path) -> None:
    main(["extract", str(tedarik_path), "--strict", "--anchor", "2026-01-01", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["eliminated"] > 0
    assert payload["item_count"] < 19


def test_extract_max_items_sinirlar(capsys: pytest.CaptureFixture[str], tedarik_path: Path) -> None:
    main(["extract", str(tedarik_path), "--max-items", "2", "--anchor", "2026-01-01"])
    out = capsys.readouterr().out
    assert "madde daha var" in out


def test_extract_lang_en(capsys: pytest.CaptureFixture[str], document_file: Callable[..., Path]) -> None:
    path = document_file("Satıcı ürünü teslim etmelidir.")
    main(["extract", str(path), "--lang", "en", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["item_count"] == 0


def test_olmayan_dosya_girdi_hatasi(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    code = main(["extract", str(tmp_path / "yok.txt")])
    assert code == 2
    assert "dosya bulunamadı" in capsys.readouterr().err


def test_bos_belge_girdi_hatasi(capsys: pytest.CaptureFixture[str], document_file: Callable[..., Path]) -> None:
    path = document_file("   \n\n")
    code = main(["extract", str(path)])
    assert code == 2
    assert "belge boş" in capsys.readouterr().err


def test_gecersiz_anchor_girdi_hatasi(capsys: pytest.CaptureFixture[str], supply_path: Path) -> None:
    code = main(["extract", str(supply_path), "--anchor", "01-01-2026"])
    assert code == 2
    assert "geçersiz anchor" in capsys.readouterr().err


def test_verify_temiz_cikti(capsys: pytest.CaptureFixture[str], data_dir: Path) -> None:
    code = main(["verify", *[str(path) for path in sorted(data_dir.glob("*.txt"))]])
    out = capsys.readouterr().out
    assert code == 0
    assert "doğrulandı" in out


def test_verify_eksik_dosya(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    assert main(["verify", str(tmp_path / "yok.txt")]) == 2
    assert "dosya bulunamadı" in capsys.readouterr().err


def test_verify_ihlalde_cikis_kodu_bir(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], supply_path: Path
) -> None:
    def fake_verify(_result: object) -> tuple[list[str], CitationStats]:
        return ["DOC1-0001: bozuk alıntı"], CitationStats(items=1, cited=0, violations=1)

    monkeypatch.setattr("clause_cite.cli.verify_citations", fake_verify)
    code = main(["verify", str(supply_path)])
    assert code == 1
    err = capsys.readouterr().err
    assert "İHLAL" in err
    assert "1 ihlal" in err


def test_module_entry_noktasi_import_edilebilir() -> None:
    module = importlib.import_module("clause_cite.__main__")
    assert callable(module.main)


def test_eval_basarili(capsys: pytest.CaptureFixture[str], golden_dir: Path) -> None:
    code = main(["eval", str(golden_dir)])
    assert code == 0
    assert "SONUÇ: 5/5" in capsys.readouterr().out


def test_eval_json(capsys: pytest.CaptureFixture[str], golden_dir: Path) -> None:
    assert main(["eval", str(golden_dir), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["cases"]) == 5


def test_eval_basarisiz(tmp_path: Path) -> None:
    (tmp_path / "d.txt").write_text("Satıcı teslim etmelidir.", encoding="utf-8")
    (tmp_path / "golden.json").write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "name": "hatalı",
                        "documents": ["d.txt"],
                        "expected": {"DOC1-0001": ["PROHIBITION", "MUST"]},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert main(["eval", str(tmp_path)]) == 1


def test_eval_olmayan_dizin(tmp_path: Path) -> None:
    assert main(["eval", str(tmp_path / "yok")]) == 2


def test_kinds_komutu(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["kinds"]) == 0
    out = capsys.readouterr().out
    assert "YÜKÜMLÜLÜK (obligation)" in out
    assert "YASAK (prohibition)" in out
    assert "toplam kalıp:" in out


def test_komut_yoksa_yardim(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 2
    assert "clause-cite" in capsys.readouterr().out


def test_surum_bayragi(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert "clause-cite" in capsys.readouterr().out
