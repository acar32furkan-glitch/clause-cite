"""Alıntı invaryantı denetimi: işaret edilemeyen şey çıkarılmaz.

Her madde için ``quote``, işaret ettiği ``start_line..end_line`` aralığındaki satırların
birleşiminde birebir geçmelidir (yalnızca beyaz boşluk normalizasyonu uygulanır). İhlaller Türkçe
mesajlarla döner; CLI bunları çıkış kodu 1'e çevirir.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict

from clause_cite.models import ExtractionResult

_WHITESPACE = re.compile(r"\s+")


class CitationStats(BaseModel):
    """Alıntı doğrulamasının özeti."""

    model_config = ConfigDict(frozen=True)

    items: int
    cited: int
    violations: int

    @property
    def coverage(self) -> float:
        """Doğrulanmış madde oranı (1.0 = tamamı; madde yoksa 1.0)."""
        if self.items == 0:
            return 1.0
        return self.cited / self.items


def _normalize(value: str) -> str:
    """Beyaz boşluk koşullarını tek boşluğa indirge (alıntı karşılaştırması için)."""
    return _WHITESPACE.sub(" ", value).strip()


def verify_citations(result: ExtractionResult) -> tuple[list[str], CitationStats]:
    """Her maddenin alıntısını kaynak satır aralığına karşı doğrula.

    Returns:
        ``(ihlal_mesajları, istatistik)``. İhlal listesi boşsa çıktı temizdir.
    """
    sources = {document.name: document for document in result.sources}
    violations: list[str] = []
    cited = 0
    for item in result.items:
        document = sources.get(item.document)
        if document is None:
            violations.append(f"{item.id}: kaynak belge bulunamadı ({item.document})")
            continue
        if not item.quote.strip():
            violations.append(f"{item.id}: alıntı boş")
            continue
        if item.start_line < 1 or item.end_line > document.line_count or item.start_line > item.end_line:
            violations.append(f"{item.id}: satır aralığı belge dışında ({item.start_line}-{item.end_line})")
            continue
        span = "\n".join(document.lines[item.start_line - 1 : item.end_line])
        if _normalize(item.quote) not in _normalize(span):
            violations.append(
                f"{item.id}: alıntı {item.document}:{item.start_line}-{item.end_line} aralığında birebir bulunamadı"
            )
            continue
        cited += 1
    return violations, CitationStats(items=len(result.items), cited=cited, violations=len(violations))


def citation_coverage(result: ExtractionResult) -> float:
    """Alıntı kapsamı: doğrulanabilen madde oranı (``%100`` beklenir)."""
    _, stats = verify_citations(result)
    return stats.coverage
