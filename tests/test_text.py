"""Belge yükleme ve cümle bölme: kısaltmalar, sayılar, satır aralıkları ve hata yolları."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from clause_cite.models import Document
from clause_cite.text import load_document, split_sentences

from .factories import doc


def texts(document: Document) -> list[str]:
    """Belgeden çıkan cümlelerin metinlerini döndür."""
    return [sentence.text for sentence in split_sentences(document)]


def test_load_document_satirlari_dondurur(document_file: Callable[..., Path]) -> None:
    path = document_file("birinci\nikinci\nüçüncü\n")
    document = load_document(path)
    assert document.lines == ("birinci", "ikinci", "üçüncü")
    assert document.name == path.name
    assert document.line_count == 3


def test_load_document_bom_temizler(document_file: Callable[..., Path]) -> None:
    path = document_file("\ufeffBaşlık\nmetin\n")
    assert load_document(path).lines[0] == "Başlık"


def test_load_document_eksik_dosya(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="bulunamadı"):
        load_document(tmp_path / "yok.txt")


def test_load_document_bos_belge(document_file: Callable[..., Path]) -> None:
    path = document_file("   \n\n\t\n")
    with pytest.raises(ValueError, match="belge boş"):
        load_document(path)


def test_load_document_uzanti_reddedilir(document_file: Callable[..., Path]) -> None:
    path = document_file("metin", "belge.pdf")
    with pytest.raises(ValueError, match="desteklenmeyen uzantı"):
        load_document(path)


def test_load_document_dizin_reddedilir(tmp_path: Path) -> None:
    folder = tmp_path / "klasor.txt"
    folder.mkdir()
    with pytest.raises(ValueError, match="dosya değil"):
        load_document(folder)


def test_load_document_utf8_hatasi(tmp_path: Path) -> None:
    path = tmp_path / "bozuk.txt"
    path.write_bytes(b"\xff\xfege\xe7ersiz")
    with pytest.raises(ValueError, match="UTF-8"):
        load_document(path)


def test_tek_cumle() -> None:
    assert texts(doc("Satıcı ürünü teslim eder.")) == ["Satıcı ürünü teslim eder."]


def test_tek_satirda_iki_cumle() -> None:
    assert texts(doc("Satıcı teslim eder. Alıcı öder.")) == ["Satıcı teslim eder.", "Alıcı öder."]


def test_satir_sonu_sinirdir() -> None:
    assert texts(doc("birinci satır\nikinci satır")) == ["birinci satır", "ikinci satır"]


def test_bos_satirlar_atlanir() -> None:
    assert texts(doc("bir\n\n\niki")) == ["bir", "iki"]


def test_kisaltma_vb_bolunmez() -> None:
    metin = "Malzeme, eldiven, maske vb. ekipman teslim edilir."
    assert texts(doc(metin)) == [metin]


def test_kisaltma_md_bolunmez() -> None:
    metin = "Md. 5 kapsamında denetim yapılır."
    assert texts(doc(metin)) == [metin]


def test_kisaltma_bkz_ve_no_bolunmez() -> None:
    metin = "bkz. Ek-1 ve No. 12 belgeler sunulur."
    assert texts(doc(metin)) == [metin]


def test_kisaltma_dr_bolunmez() -> None:
    metin = "Dr. Ayşe Yılmaz denetim yapar."
    assert texts(doc(metin)) == [metin]


def test_ondalik_sayi_bolunmez() -> None:
    metin = "Ceza 1.234,56 TL olarak uygulanır."
    assert texts(doc(metin)) == [metin]


def test_tarih_noktalari_bolunmez() -> None:
    metin = "Teslim en geç 15.03.2026 tarihine kadar yapılır."
    assert texts(doc(metin)) == [metin]


def test_satir_araligi_korunur() -> None:
    document = doc("başlık\nbirinci cümle. ikinci cümle.\nson satır")
    sentences = split_sentences(document)
    assert [(s.start_line, s.end_line) for s in sentences] == [(1, 1), (2, 2), (2, 2), (3, 3)]


def test_cumle_metni_kaynak_satirin_parcasidir() -> None:
    line = "Satıcı teslim eder. Alıcı öder."
    document = doc(line)
    for sentence in split_sentences(document):
        assert sentence.text in line


def test_bos_belge_cumle_uretmez() -> None:
    assert split_sentences(doc("\n\n  \n")) == []


def test_unlem_ve_soru_isareti_boler() -> None:
    assert texts(doc("Teslim edildi mi? Edilmedi!")) == ["Teslim edildi mi?", "Edilmedi!"]
