"""Kalıp kataloğu: her tür ve kip için TR ve EN kapsaması, dil filtresi."""

from __future__ import annotations

import pytest

from clause_cite.models import ItemKind, Modality
from clause_cite.patterns import (
    COMPILED,
    PATTERNS,
    compile_patterns,
    kinds_overview,
    match_patterns,
    patterns_for,
)


def signals(text: str, *, lang: str = "auto") -> list[str]:
    """Eşleşen kalıpların sinyal adlarını döndür."""
    return [matcher.signal for matcher in match_patterns(text, lang=lang)]


def kinds(text: str, *, lang: str = "auto") -> set[ItemKind]:
    """Eşleşen kalıpların türlerini döndür."""
    return {matcher.kind for matcher in match_patterns(text, lang=lang)}


def modalities(text: str, *, lang: str = "auto") -> set[Modality]:
    """Eşleşen kalıpların kiplerini döndür."""
    return {matcher.modality for matcher in match_patterns(text, lang=lang)}


def test_tr_melidir_yukumluluk_must() -> None:
    assert "tr_melidir" in signals("Satıcı teslim etmelidir.")
    assert kinds("Satıcı teslim etmelidir.") == {ItemKind.OBLIGATION}
    assert modalities("Satıcı teslim etmelidir.") == {Modality.MUST}


def test_tr_meli_onerilen_should() -> None:
    matches = match_patterns("Taraflar dikkatli olmalı.")
    assert any(matcher.signal == "tr_meli" and matcher.modality is Modality.SHOULD for matcher in matches)


def test_tr_melidir_meli_ile_karismaz() -> None:
    assert "tr_meli" not in signals("Satıcı teslim etmelidir.")


def test_tr_zorundadir_ve_yukumludur() -> None:
    assert "tr_zorundadir" in signals("Satıcı teslim etmek zorundadır.")
    assert "tr_yukumludur" in signals("Satıcı teslim etmekle yükümlüdür.")


def test_tr_yukumluluk_basligi_yanlis_alarm_uretmez() -> None:
    assert signals("Genel Yükümlülükler") == []


def test_tr_yasaktir_prohibition() -> None:
    assert kinds("Bilgi paylaşması yasaktır.") == {ItemKind.PROHIBITION}


def test_tr_mamali_prohibition() -> None:
    assert ItemKind.PROHIBITION in kinds("Yüklenici denetime engel olmamalıdır.")


def test_tr_edemez_prohibition() -> None:
    assert "tr_edemez" in signals("Satıcı itiraz edemez.")


def test_tr_izin_verilmez_prohibition() -> None:
    assert "tr_izin_verilmez" in signals("Üçüncü kişilere izin verilmez.")


def test_tr_abilir_izin_may() -> None:
    matches = match_patterns("Satıcı ceza talep edebilir.")
    assert any(matcher.signal == "tr_abilir" and matcher.modality is Modality.MAY for matcher in matches)


def test_tr_hakki_vardir_may() -> None:
    assert "tr_hakki_vardir" in signals("Satıcının denetim hakkı vardır.")


def test_tr_termin_kaliplari() -> None:
    assert "tr_en_gec" in signals("Teslim en geç 15.03.2026 tarihine kadar yapılır.")
    assert "tr_tarihine_kadar" in signals("Teslim 15.03.2026 tarihine kadar yapılır.")
    assert "tr_gun_icinde" in signals("Ödeme 30 gün içinde yapılır.")


def test_tr_belge_zorunlulugu() -> None:
    assert kinds("Faturanın sunulması zorunludur.") == {ItemKind.DOCUMENT_REQUIRED}
    assert "tr_belge_zorunlu" in signals("Belgelerin teslim edilmesi gerekir.")


def test_tr_tanim() -> None:
    assert kinds('"Hizmet" temizlik faaliyetlerini ifade eder.') == {ItemKind.DEFINITION}


def test_tr_belirsiz() -> None:
    assert kinds("Ek hizmetler makul süre içinde belirlenir.") == {ItemKind.AMBIGUOUS}


def test_tr_para_dil_bagimsiz() -> None:
    assert kinds("Ceza 1.234,56 TL'dir.") == {ItemKind.MONEY}


def test_en_shall_ve_must() -> None:
    assert "en_shall" in signals("The Seller shall deliver the goods.")
    assert "en_must" in signals("The Buyer must pay the invoice.")
    assert modalities("The Seller shall deliver the goods.") == {Modality.MUST}


def test_en_shall_not_ve_must_not_prohibition() -> None:
    assert ItemKind.PROHIBITION in kinds("The Seller shall not disclose information.")
    assert ItemKind.PROHIBITION in kinds("The Buyer must not withhold payment.")


def test_en_may_not_prohibition() -> None:
    assert "en_may_not" in signals("The Buyer may not assign this agreement.")


def test_en_prohibited() -> None:
    assert kinds("Disclosure of information is prohibited.") == {ItemKind.PROHIBITION}


def test_en_may_izin_may() -> None:
    matches = match_patterns("The Buyer may reject the goods.")
    assert any(matcher.signal == "en_may" and matcher.modality is Modality.MAY for matcher in matches)


def test_en_should_ve_entitled_to() -> None:
    assert any(matcher.modality is Modality.SHOULD for matcher in match_patterns("The Buyer should notify the Seller."))
    assert "en_entitled_to" in signals("The Seller is entitled to charge interest.")


def test_en_required_to() -> None:
    assert "en_required_to" in signals("The Buyer is required to acknowledge receipt.")


def test_en_termin_kaliplari() -> None:
    assert "en_within" in signals("The Buyer shall pay within 30 days.")
    assert "en_no_later_than" in signals("Delivery is due no later than 15 March 2026.")
    assert "en_by_date" in signals("Delivery is due by 15.03.2026.")


def test_en_belge_zorunlulugu() -> None:
    assert ItemKind.DOCUMENT_REQUIRED in kinds("The Seller must submit the certificate.")
    assert "en_belge_zorunlu" in signals("The Seller shall provide the delivery note.")


def test_en_tanim() -> None:
    assert kinds("The agreement is defined as the entire understanding.") == {ItemKind.DEFINITION}


def test_en_belirsiz() -> None:
    assert kinds("The schedule is to be agreed later.") == {ItemKind.AMBIGUOUS}


def test_dil_filtresi_en() -> None:
    assert signals("Satıcı teslim etmelidir.", lang="en") == []
    assert "en_shall" not in signals("The Seller shall deliver.", lang="tr")


def test_para_kalibi_dil_filtresinden_etkilenmez() -> None:
    assert "money" in signals("Ceza 1.234,56 TL'dir.", lang="tr")
    assert "money" in signals("A fee of USD 5,000 applies.", lang="en")


def test_gecersiz_dil_hata() -> None:
    with pytest.raises(ValueError, match="geçersiz dil"):
        match_patterns("metin", lang="de")


def test_tum_kaliplar_derlenir() -> None:
    assert len(COMPILED) == len(PATTERNS)
    assert compile_patterns(()) == ()


def test_her_kalip_sinyal_adi_tek() -> None:
    names = [pattern.signal for pattern in PATTERNS]
    assert len(names) == len(set(names))


def test_her_kalip_derlenebilir() -> None:
    for matcher in COMPILED:
        assert matcher.regex.pattern


def test_patterns_for_turleri_filtreler() -> None:
    assert all(pattern.kind is ItemKind.DEADLINE for pattern in patterns_for(ItemKind.DEADLINE))
    assert len(patterns_for(ItemKind.DEADLINE)) >= 2


def test_kinds_overview_tum_turleri_kapsar() -> None:
    overview = kinds_overview()
    assert [kind for kind, _ in overview] == list(ItemKind)
    assert all(patterns for _, patterns in overview)
