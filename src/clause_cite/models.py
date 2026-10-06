"""Çıkarım motorunun veri modelleri.

Tasarım ilkesi: **alıntısız madde var olamaz.** Her `Item`, kaynak belgede ``start_line..end_line``
aralığında birebir geçen bir metni (``quote``) taşır; bu yüzden `verify.py` çıktının tamamını
kaynak metne karşı doğrulayabilir. Alan adları ve kod sabitleri İngilizcedir (CI kaydı ve kod için),
kullanıcıya dönük etiketler (``label_tr``) Türkçedir.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Modality(StrEnum):
    """Yükümlülük kipi. ``may``/``should``/``must`` asla birleştirilmez; her madde kipini korur."""

    MUST = "must"
    SHOULD = "should"
    MAY = "may"

    @property
    def label_tr(self) -> str:
        """Türkçe kip etiketi."""
        return _MODALITY_LABELS[self.value]


_MODALITY_LABELS: dict[str, str] = {
    "must": "ZORUNLU",
    "should": "ÖNERİLEN",
    "may": "OPSİYONEL",
}


class ItemKind(StrEnum):
    """Aksiyon maddesinin türü."""

    OBLIGATION = "obligation"
    PROHIBITION = "prohibition"
    DEADLINE = "deadline"
    MONEY = "money"
    DOCUMENT_REQUIRED = "document_required"
    DEFINITION = "definition"
    AMBIGUOUS = "ambiguous"

    @property
    def label_tr(self) -> str:
        """Türkçe tür etiketi."""
        return _KIND_LABELS[self.value]


_KIND_LABELS: dict[str, str] = {
    "obligation": "YÜKÜMLÜLÜK",
    "prohibition": "YASAK",
    "deadline": "TERMİN",
    "money": "PARA",
    "document_required": "BELGE_ZORUNLU",
    "definition": "TANIM",
    "ambiguous": "BELİRSİZ",
}


class Confidence(StrEnum):
    """Çıkarımın güven düzeyi; düşük güven `needs_review` ile işaretlenir."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @property
    def label_tr(self) -> str:
        """Türkçe güven etiketi."""
        return _CONFIDENCE_LABELS[self.value]


_CONFIDENCE_LABELS: dict[str, str] = {
    "high": "YÜKSEK",
    "medium": "ORTA",
    "low": "DÜŞÜK",
}


class Document(BaseModel):
    """Tek bir kaynak belge. Satırlar 1 tabanlıdır: satır numarası = ``lines`` indeksi + 1."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    path: str
    lines: tuple[str, ...]

    @property
    def line_count(self) -> int:
        """Belgedeki satır sayısı."""
        return len(self.lines)

    def line(self, number: int) -> str:
        """1 tabanlı satır numarasına göre satırı döndür."""
        return self.lines[number - 1]


class Sentence(BaseModel):
    """Belgeden çıkarılmış tek bir cümle ve kaynak belgedeki gerçek satır aralığı."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str
    start_line: int
    end_line: int


class Item(BaseModel):
    """Kanıtlı tek bir aksiyon maddesi: metin + birebir alıntı + kaynak satır aralığı."""

    model_config = ConfigDict(frozen=True)

    id: str
    kind: ItemKind
    modality: Modality
    text: str
    quote: str
    document: str
    start_line: int
    end_line: int
    actor: str | None = None
    actor_resolved: bool = True
    due_date: date | None = None
    due_raw: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    confidence: Confidence = Confidence.HIGH
    needs_review: bool = False
    signals: tuple[str, ...] = ()

    @property
    def is_unresolved(self) -> bool:
        """Taraf ya da tarih çözülemediyse ``True`` (madde ``unresolved`` sayılır)."""
        if not self.actor_resolved:
            return True
        return self.due_raw is not None and self.due_date is None

    @property
    def citation(self) -> str:
        """İnsan okur biçiminde atıf: ``dosya:satır-satır``."""
        return f"{self.document}:{self.start_line}-{self.end_line}"


class ExtractionResult(BaseModel):
    """Bir çıkarım çalışmasının tamamı: maddeler, kaynaklar ve özet istatistikler."""

    model_config = ConfigDict(frozen=True)

    items: tuple[Item, ...]
    documents: tuple[str, ...]
    sentences: int
    sources: tuple[Document, ...] = ()
    stats: dict[str, int] = Field(default_factory=dict)

    def count(self, kind: ItemKind) -> int:
        """Verilen türdeki madde sayısı."""
        return sum(1 for item in self.items if item.kind is kind)

    def by_kind(self) -> dict[ItemKind, int]:
        """Tür → madde sayısı dağılımı (boş türler 0 ile yer alır)."""
        counts: dict[ItemKind, int] = dict.fromkeys(ItemKind, 0)
        for item in self.items:
            counts[item.kind] += 1
        return counts

    def unresolved_count(self) -> int:
        """Tarafı ya da tarihi çözülemeyen madde sayısı."""
        return sum(1 for item in self.items if item.is_unresolved)

    def unresolved_ids(self) -> tuple[str, ...]:
        """Çözülemeyen maddelerin kimlikleri (altın set karşılaştırması için)."""
        return tuple(item.id for item in self.items if item.is_unresolved)

    def eliminated_count(self) -> int:
        """``strict`` modunda elenen madde sayısı (sessizce yok olmaz, burada sayılır)."""
        return self.stats.get("eliminated", 0)
