"""Çıkarım motoru: kip korunumu, öncelik, aktör/tarih/tutar, tekilleştirme, determinizm."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from clause_cite.extract import (
    detect_actor,
    extract,
    pick_kind,
    pick_modality,
    resolve_amount,
    resolve_date,
    score_confidence,
)
from clause_cite.models import Confidence, Item, ItemKind, Modality
from clause_cite.patterns import match_patterns

from .factories import doc, docs, items_of

ANCHOR = date(2026, 1, 1)


def one(text: str, *, anchor: date | None = None) -> Item:
    """Tek satırlık bir belgeden çıkan ilk maddeyi döndür."""
    result = extract((doc(text),), anchor=anchor)
    assert len(result.items) == 1
    return result.items[0]


def test_kip_must_korunur() -> None:
    item = one("The Buyer must pay the invoice.")
    assert item.modality is Modality.MUST


def test_kip_may_korunur() -> None:
    item = one("The Buyer may reject the goods.")
    assert item.modality is Modality.MAY


def test_kip_should_korunur() -> None:
    item = one("The Buyer should notify the Seller.")
    assert item.modality is Modality.SHOULD


def test_yasak_yukumlulukten_once() -> None:
    item = one("The Seller shall deliver the goods and shall not disclose information.")
    assert item.kind is ItemKind.PROHIBITION
    assert item.modality is Modality.MUST


def test_belge_zorunlulugu_yukumlulukten_once() -> None:
    item = one("The Seller shall provide the delivery note.")
    assert item.kind is ItemKind.DOCUMENT_REQUIRED


def test_yukumluluk_terminden_once() -> None:
    item = one("Satıcı, ürünleri en geç 15.03.2026 tarihine kadar teslim etmelidir.")
    assert item.kind is ItemKind.OBLIGATION


def test_kip_onceligi_must_uzerinden_may() -> None:
    item = one("The Seller shall deliver and may charge interest.")
    assert item.modality is Modality.MUST


def test_signals_tum_kaliplari_icerir() -> None:
    item = one("The Buyer shall not withhold payment.")
    assert "en_shall_not" in item.signals
    assert "en_shall" in item.signals


def test_aktor_tr_tespit() -> None:
    assert detect_actor("Satıcı ürünü teslim eder.") == ("Satıcı", True)
    assert detect_actor("Yüklenici hizmeti sunar.") == ("Yüklenici", True)
    assert detect_actor("İdare ödemeyi yapar.") == ("İdare", True)


def test_aktor_en_tespit() -> None:
    assert detect_actor("The Seller shall deliver.") == ("Seller", True)
    assert detect_actor("The Buyer must pay.") == ("Buyer", True)


def test_aktor_yoksa_cozulmus_sayilir() -> None:
    assert detect_actor("Fatura teslim edilir.") == (None, True)


def test_cozulemeyen_taraf_isaretlenir() -> None:
    item = one("Ek hizmetler ilgili taraf tarafından yerine getirilmelidir.")
    assert item.actor is None
    assert item.actor_resolved is False
    assert item.is_unresolved is True


def test_tek_cumlede_tekrar_eden_madde_tekillesir() -> None:
    result = extract((doc("Satıcı ödemelidir ve teslim etmelidir."),))
    assert len(result.items) == 1
    assert result.items[0].signals == ("tr_melidir",)


def test_birebir_ayni_cumle_tekillesir() -> None:
    result = extract((doc("Satıcı ödemelidir. Satıcı ödemelidir."),))
    assert len(result.items) == 1


def test_kimlik_bicimi() -> None:
    result = extract((doc("Satıcı teslim etmelidir.\nAlıcı ödemelidir."),))
    assert [item.id for item in result.items] == ["DOC1-0001", "DOC1-0002"]


def test_birden_cok_belge_onek_alir() -> None:
    result = extract(docs("Satıcı teslim etmelidir.", "The Buyer must pay."))
    assert [item.id for item in result.items] == ["DOC1-0001", "DOC2-0001"]
    assert result.documents == ("belge1.txt", "belge2.txt")


def test_determinizm() -> None:
    text = "Satıcı, cezayı en geç 15.03.2026 tarihine kadar ödemelidir."
    first = extract((doc(text),), anchor=ANCHOR)
    second = extract((doc(text),), anchor=ANCHOR)
    assert first.model_dump() == second.model_dump()


def test_strict_yalnizca_yuksek_guven_birakir() -> None:
    text = "Satıcı, cezayı en geç 15.03.2026 tarihine kadar ödemelidir.\nSatıcı ödemelidir."
    loose = extract((doc(text),), anchor=ANCHOR)
    strict = extract((doc(text),), anchor=ANCHOR, strict=True)
    assert len(loose.items) == 2
    assert len(strict.items) == 1
    assert strict.items[0].confidence is Confidence.HIGH
    assert strict.eliminated_count() == 1


def test_strict_olmayan_modda_eleme_sayaci_yok() -> None:
    result = extract((doc("Satıcı ödemelidir."),))
    assert result.eliminated_count() == 0
    assert "eliminated" not in result.stats


def test_alinti_kaynak_satirdan_birebir() -> None:
    line = "Satıcı ürünleri teslim etmelidir."
    document = doc(line)
    result = extract((document,))
    item = result.items[0]
    assert item.quote in document.lines[item.start_line - 1]
    assert item.citation == "belge.txt:1-1"


def test_satir_araligi_dogru() -> None:
    document = doc("başlık\nSatıcı teslim etmelidir.")
    result = extract((document,))
    assert result.items[0].start_line == 2
    assert result.items[0].end_line == 2


def test_tutar_zenginlestirme() -> None:
    item = one("Satıcı 1.234,56 TL ceza ödeyebilir.")
    assert item.amount == Decimal("1234.56")
    assert item.currency == "TL"


def test_mutlak_tarih_zenginlestirme() -> None:
    item = one("Teslim en geç 15.03.2026 tarihine kadar yapılmalıdır.")
    assert item.due_date == date(2026, 3, 15)
    assert item.due_raw == "15.03.2026"


def test_goreli_tarih_anchor_ile_cozulur() -> None:
    item = one("Satıcı 30 gün içinde teslim etmelidir.", anchor=ANCHOR)
    assert item.due_date == date(2026, 1, 31)
    assert item.is_unresolved is False


def test_goreli_tarih_anchor_yoksa_unresolved() -> None:
    item = one("Satıcı 30 gün içinde teslim etmelidir.")
    assert item.due_date is None
    assert item.due_raw == "30 gün içinde"
    assert item.is_unresolved is True
    assert item.needs_review is True


def test_dusuk_guven_inceleme_ister() -> None:
    item = one("Ağır ihlaller halinde sözleşme feshedilebilir.")
    assert item.confidence is Confidence.LOW
    assert item.needs_review is True


def test_kalipsiz_cumle_madde_uretmez() -> None:
    result = extract((doc("Bu cümlede hiçbir kalıp yok.\nBaşka bir düz cümle."),))
    assert result.items == ()
    assert result.sentences == 2


def test_bos_girdi_bos_sonuc() -> None:
    result = extract(())
    assert result.items == ()
    assert result.documents == ()
    assert result.sentences == 0


def test_dil_filtresi_tr_ingilizce_cumleyi_atlar() -> None:
    result = extract((doc("The Buyer must pay the invoice."),), lang="tr")
    assert result.items == ()


def test_dil_filtresi_en_turkce_cumleyi_atlar() -> None:
    result = extract((doc("Satıcı teslim etmelidir."),), lang="en")
    assert result.items == ()


def test_sentences_sayaci() -> None:
    result = extract((doc("Bir cümle. İki cümle.\nÜç cümle."),))
    assert result.sentences == 3


def test_pick_kind_oncelik() -> None:
    matches = match_patterns("The Seller shall provide the delivery note.")
    assert pick_kind(matches) is ItemKind.DOCUMENT_REQUIRED


def test_pick_kind_bos_liste_belirsiz() -> None:
    assert pick_kind([]) is ItemKind.AMBIGUOUS


def test_pick_modality_oncelik() -> None:
    matches = match_patterns("The Seller shall deliver and may charge interest.")
    assert pick_modality(matches) is Modality.MUST


def test_pick_modality_bos_liste_may() -> None:
    assert pick_modality([]) is Modality.MAY


def test_resolve_date_mutlak_ve_goreli() -> None:
    assert resolve_date("Teslim 15.03.2026 tarihinde yapılır.", anchor=None) == (date(2026, 3, 15), "15.03.2026")
    assert resolve_date("Teslim 30 gün içinde yapılır.", anchor=ANCHOR) == (date(2026, 1, 31), "30 gün içinde")
    assert resolve_date("Teslim yakında yapılır.", anchor=ANCHOR) == (None, None)


def test_resolve_amount_yok() -> None:
    assert resolve_amount("Tutar belirtilmemiştir.") == (None, None)


def test_confidence_yuksek_sinyal_ve_aktor() -> None:
    assert (
        score_confidence(signal_count=2, actor="Satıcı", actor_resolved=True, due_date=None, due_raw=None, amount=None)
        is Confidence.HIGH
    )


def test_confidence_cozulemeyen_goreli_tarih_dusurur() -> None:
    assert (
        score_confidence(
            signal_count=1, actor="Satıcı", actor_resolved=True, due_date=None, due_raw="30 gün içinde", amount=None
        )
        is Confidence.LOW
    )


def test_items_of_yardimcisi() -> None:
    result = extract((doc("Satıcı teslim etmelidir."),))
    assert len(items_of(result)) == 1
