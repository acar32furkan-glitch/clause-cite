"""Çıktı biçimleri: alıntı ve atıf görünür mü, CSV/Markdown/JSON sözleşmesi doğru mu."""

from __future__ import annotations

import csv
import io
import json
from datetime import date

from clause_cite.extract import extract
from clause_cite.models import ExtractionResult, Item, ItemKind, Modality
from clause_cite.render import (
    render_csv,
    render_github_summary,
    render_json_payload,
    render_markdown,
    render_text,
)

from .factories import doc

ANCHOR = date(2026, 1, 1)
SAMPLE = (
    "Satıcı, cezayı en geç 15.03.2026 tarihine kadar 1.234,56 TL olarak ödemelidir.\nAlıcı ürünü teslim almamalıdır."
)


def sample_result() -> ExtractionResult:
    """İki maddelik örnek sonuç."""
    return extract((doc(SAMPLE),), anchor=ANCHOR)


def test_render_text_alinti_ve_atif_gosterir() -> None:
    text = render_text(sample_result())
    assert 'alıntı: "Satıcı, cezayı en geç 15.03.2026 tarihine kadar 1.234,56 TL olarak ödemelidir."' in text
    assert "belge.txt:1-1" in text
    assert "ÇIKARILAN AKSİYON MADDELERİ" in text


def test_render_text_tur_bazli_gruplar() -> None:
    text = render_text(sample_result())
    assert "YÜKÜMLÜLÜK (obligation)" in text
    assert "YASAK (prohibition)" in text


def test_render_text_aktor_tarih_tutar() -> None:
    text = render_text(sample_result())
    assert "aktör: Satıcı" in text
    assert "termin: 2026-03-15" in text
    assert "tutar: 1234.56 TL" in text


def test_render_text_max_items_sinirlar() -> None:
    text = render_text(sample_result(), max_items=1)
    assert "madde daha var" in text
    assert "Alıcı ürünü teslim almamalıdır." not in text


def test_render_text_bos_sonuc() -> None:
    text = render_text(ExtractionResult(items=(), documents=(), sentences=0))
    assert "Madde bulunamadı." in text


def test_render_text_cozulemeyen_aktor_gosterir() -> None:
    result = extract((doc("Ek hizmetler ilgili taraf tarafından yerine getirilmelidir."),))
    assert "aktör: (çözülemedi)" in render_text(result)


def test_render_text_anchor_siz_termin() -> None:
    result = extract((doc("Satıcı 30 gün içinde teslim etmelidir."),))
    assert "(anchor yok)" in render_text(result)


def test_render_text_sinyalsiz_madde_yazilir() -> None:
    item = Item(
        id="DOC1-0001",
        kind=ItemKind.OBLIGATION,
        modality=Modality.MUST,
        text="elyazması madde",
        quote="elyazması madde",
        document="belge.txt",
        start_line=1,
        end_line=1,
    )
    result = ExtractionResult(items=(item,), documents=("belge.txt",), sentences=1, sources=(doc("elyazması madde"),))
    text = render_text(result)
    assert "elyazması madde" in text
    assert "sinyal:" not in text


def test_render_text_strict_eleme_satiri() -> None:
    result = extract((doc(SAMPLE),), anchor=ANCHOR, strict=True)
    text = render_text(result)
    assert "--strict ile elenen madde" in text


def test_render_csv_baslik_ve_satirlar() -> None:
    rows = list(csv.reader(io.StringIO(render_csv(sample_result()))))
    assert rows[0][0] == "id"
    assert "quote" in rows[0]
    assert len(rows) == 3  # başlık + 2 madde
    assert rows[1][-1].startswith("Satıcı")


def test_render_markdown_tablo_ve_baslik() -> None:
    markdown = render_markdown(sample_result())
    assert "### Kanıtlı aksiyon maddeleri" in markdown
    assert "| Kimlik | Tür | Kip |" in markdown
    assert "belge.txt:1-1" in markdown


def test_render_github_summary_basligi() -> None:
    assert "### Kanıtlı aksiyon maddeleri" in render_github_summary(sample_result())


def test_render_text_tanim_maddesinde_kip_etiketi_yok() -> None:
    """Tanım cümlesi opsiyonel/zorunlu değildir: insan tarafında kip etiketi basılmamalı."""
    result = extract((doc('"Hizmet", temizlik faaliyetlerini ifade eder.'),))
    text = render_text(result)
    assert "TANIM (definition)" in text
    assert "TANIM" in text
    assert "OPSİYONEL" not in text
    assert "] — ·" in text or "] —" in text


def test_render_text_aktoru_belirtilmemis_madde() -> None:
    """Aktörü hiç geçmeyen cümle 'çözülemedi' değil 'metinde belirtilmemiş' olarak görünmeli."""
    result = extract((doc("Primler zamanında ödenmelidir."),))
    text = render_text(result)
    assert "aktör: (metinde belirtilmemiş)" in text
    assert "aktör: (çözülemedi)" not in text


def test_render_json_payload_sozlesmesi() -> None:
    payload = render_json_payload(sample_result(), anchor=ANCHOR)
    assert set(payload) >= {
        "version",
        "anchor",
        "documents",
        "sentences",
        "item_count",
        "unresolved",
        "eliminated",
        "coverage",
        "counts",
        "items",
    }
    assert payload["anchor"] == "2026-01-01"
    assert payload["item_count"] == 2
    assert payload["coverage"] == 1.0
    assert payload["counts"]["obligation"] == 1
    assert payload["items"][0]["id"] == "DOC1-0001"


def test_render_json_payload_anchor_yok() -> None:
    payload = render_json_payload(sample_result(), anchor=None)
    assert payload["anchor"] is None


def test_render_json_serilestirilebilir() -> None:
    payload = render_json_payload(sample_result(), anchor=ANCHOR)
    text = json.dumps(payload, ensure_ascii=False)
    assert "DOC1-0001" in text
