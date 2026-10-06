"""Model yardımcıları: etiketler, satır erişimi, çözülemeyen madde ve sayaçlar."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from clause_cite.models import (
    Confidence,
    Document,
    ExtractionResult,
    Item,
    ItemKind,
    Modality,
)


def make_item(item_id: str = "DOC1-0001", **overrides: object) -> Item:
    """Varsayılanları doldurulmuş bir madde üret."""
    payload: dict[str, object] = {
        "id": item_id,
        "kind": ItemKind.OBLIGATION,
        "modality": Modality.MUST,
        "text": "Satıcı teslim etmelidir.",
        "quote": "Satıcı teslim etmelidir.",
        "document": "belge.txt",
        "start_line": 3,
        "end_line": 3,
    }
    payload.update(overrides)
    return Item.model_validate(payload)


def test_modality_etiketleri() -> None:
    assert Modality.MUST.label_tr == "ZORUNLU"
    assert Modality.SHOULD.label_tr == "ÖNERİLEN"
    assert Modality.MAY.label_tr == "OPSİYONEL"


def test_modality_degerleri_ingilizce() -> None:
    assert [member.value for member in Modality] == ["must", "should", "may"]


def test_itemkind_etiketleri() -> None:
    assert ItemKind.OBLIGATION.label_tr == "YÜKÜMLÜLÜK"
    assert ItemKind.PROHIBITION.label_tr == "YASAK"
    assert ItemKind.DEADLINE.label_tr == "TERMİN"
    assert ItemKind.MONEY.label_tr == "PARA"
    assert ItemKind.DOCUMENT_REQUIRED.label_tr == "BELGE_ZORUNLU"
    assert ItemKind.DEFINITION.label_tr == "TANIM"
    assert ItemKind.AMBIGUOUS.label_tr == "BELİRSİZ"


def test_confidence_etiketleri() -> None:
    assert Confidence.HIGH.label_tr == "YÜKSEK"
    assert Confidence.MEDIUM.label_tr == "ORTA"
    assert Confidence.LOW.label_tr == "DÜŞÜK"


def test_document_satir_erisimi() -> None:
    document = Document(name="a.txt", path="a.txt", lines=("bir", "iki", "üç"))
    assert document.line_count == 3
    assert document.line(2) == "iki"


def test_item_citation_bicimi() -> None:
    item = make_item(start_line=7, end_line=9)
    assert item.citation == "belge.txt:7-9"


def test_item_varsayilan_alanlar() -> None:
    item = make_item()
    assert item.actor is None
    assert item.actor_resolved is True
    assert item.confidence is Confidence.HIGH
    assert item.needs_review is False
    assert item.signals == ()
    assert item.amount is None


def test_cozumlenemeyen_taraf_unresolved() -> None:
    item = make_item(actor_resolved=False)
    assert item.is_unresolved is True


def test_anchor_siz_goreli_tarih_unresolved() -> None:
    item = make_item(due_raw="30 gün içinde", due_date=None)
    assert item.is_unresolved is True
    assert make_item(due_raw="30 gün içinde", due_date=date(2026, 1, 31)).is_unresolved is False


def test_extraction_result_sayaclari() -> None:
    items = (
        make_item("DOC1-0001"),
        make_item("DOC1-0002", kind=ItemKind.PROHIBITION),
        make_item("DOC1-0003", kind=ItemKind.DEADLINE, actor_resolved=False),
    )
    result = ExtractionResult(items=items, documents=("belge.txt",), sentences=10)
    assert result.count(ItemKind.OBLIGATION) == 1
    assert result.count(ItemKind.PROHIBITION) == 1
    counts = result.by_kind()
    assert counts[ItemKind.OBLIGATION] == 1
    assert counts[ItemKind.DEADLINE] == 1
    assert counts[ItemKind.AMBIGUOUS] == 0
    assert result.unresolved_count() == 1
    assert result.unresolved_ids() == ("DOC1-0003",)


def test_strict_elenen_sayisi() -> None:
    result = ExtractionResult(items=(), documents=(), sentences=0, stats={"eliminated": 4})
    assert result.eliminated_count() == 4
    assert ExtractionResult(items=(), documents=(), sentences=0).eliminated_count() == 0


def test_tutar_decimal_kalir() -> None:
    item = make_item(amount=Decimal("1234.56"), currency="TL")
    assert isinstance(item.amount, Decimal)
    assert item.amount == Decimal("1234.56")
