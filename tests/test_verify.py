"""Alıntı invaryantı: kasıtlı bozuk alıntı, kaynak yokluğu, aralık taşması."""

from __future__ import annotations

from clause_cite.extract import extract
from clause_cite.models import ExtractionResult
from clause_cite.verify import CitationStats, citation_coverage, verify_citations

from .factories import doc


def base_result() -> ExtractionResult:
    """Tek maddelik temiz bir sonuç üret."""
    return extract((doc("başlık\nSatıcı ürünleri teslim etmelidir."),))


def tamper(
    result: ExtractionResult,
    *,
    quote: str | None = None,
    document: str | None = None,
    start: int | None = None,
    end: int | None = None,
) -> ExtractionResult:
    """İlk maddeyi kasıtlı bozarak yeni bir sonuç üret."""
    updates: dict[str, object] = {}
    if quote is not None:
        updates["quote"] = quote
    if document is not None:
        updates["document"] = document
    if start is not None:
        updates["start_line"] = start
    if end is not None:
        updates["end_line"] = end
    broken = result.items[0].model_copy(update=updates)
    return result.model_copy(update={"items": (broken, *result.items[1:])})


def test_temiz_sonuc_ihlal_uretmez() -> None:
    violations, stats = verify_citations(base_result())
    assert violations == []
    assert stats.items == 1
    assert stats.cited == 1
    assert stats.coverage == 1.0


def test_kapsam_yuzde_yuz() -> None:
    assert citation_coverage(base_result()) == 1.0


def test_bozuk_alinti_yakalanir() -> None:
    result = tamper(base_result(), quote="Bu metin kaynakta yok.")
    violations, stats = verify_citations(result)
    assert len(violations) == 1
    assert "birebir bulunamadı" in violations[0]
    assert stats.cited == 0
    assert stats.violations == 1


def test_bos_alinti_yakalanir() -> None:
    violations, _ = verify_citations(tamper(base_result(), quote="   "))
    assert len(violations) == 1
    assert "alıntı boş" in violations[0]


def test_kaynak_belge_yoksa_yakalanir() -> None:
    violations, _ = verify_citations(tamper(base_result(), document="yok.txt"))
    assert len(violations) == 1
    assert "kaynak belge bulunamadı" in violations[0]


def test_aralik_belge_disinda_yakalanir() -> None:
    violations, _ = verify_citations(tamper(base_result(), end=99))
    assert len(violations) == 1
    assert "satır aralığı belge dışında" in violations[0]


def test_baslangic_sondan_buyukse_yakalanir() -> None:
    violations, _ = verify_citations(tamper(base_result(), start=5, end=2))
    assert len(violations) == 1
    assert "satır aralığı belge dışında" in violations[0]


def test_dogru_satir_araligi_dogrulanir() -> None:
    result = base_result()
    item = result.items[0]
    assert item.start_line == 2
    assert verify_citations(result)[0] == []


def test_bos_sonuc_kapsami_tam() -> None:
    empty = ExtractionResult(items=(), documents=(), sentences=0)
    violations, stats = verify_citations(empty)
    assert violations == []
    assert stats.coverage == 1.0


def test_citation_stats_varsayilanlari() -> None:
    stats = CitationStats(items=0, cited=0, violations=0)
    assert stats.coverage == 1.0
