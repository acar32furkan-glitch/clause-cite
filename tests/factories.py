"""Test kurucuları: kısa ve okunur belge/cümle üretimi.

Testler üretim kodundaki örnek dosyalara bağlı kalmak zorunda değildir; burada kurulan minik
belgeler her kuralın sınır davranışını tek bakışta görünür kılar.
"""

from __future__ import annotations

from clause_cite.models import Document, ExtractionResult, Item


def doc(text: str, *, name: str = "belge.txt") -> Document:
    """Çok satırlı bir metni tek satırlık alanlara bölerek ``Document`` üret."""
    return Document(name=name, path=name, lines=tuple(text.splitlines()))


def docs(*texts: str) -> tuple[Document, ...]:
    """Birden çok metni sıralı belgelere çevir (``DOC1``, ``DOC2`` ... önekleri bu sıraya bağlıdır)."""
    return tuple(doc(text, name=f"belge{index}.txt") for index, text in enumerate(texts, start=1))


def items_of(result: ExtractionResult) -> list[Item]:
    """Sonuçtaki maddeleri liste olarak döndür."""
    return list(result.items)
