"""Tarih çözümleme: mutlak biçimler, göreli terminler, anchor davranışı, belirsizlik."""

from __future__ import annotations

from datetime import date

import pytest

from clause_cite.dates import find_absolute, parse_absolute, parse_relative

ANCHOR = date(2026, 1, 1)


def test_mutlak_noktali() -> None:
    assert parse_absolute("Teslim en geç 15.03.2026 tarihine kadar yapılır.") == date(2026, 3, 15)


def test_mutlak_iso() -> None:
    assert parse_absolute("Yürürlük 2026-03-15 tarihinde başlar.") == date(2026, 3, 15)


def test_mutlak_tr_ay_adi() -> None:
    assert parse_absolute("Sözleşme 15 Mart 2026 tarihinde imzalanır.") == date(2026, 3, 15)


def test_mutlak_tr_ay_adi_agustos() -> None:
    assert parse_absolute("İmza 3 Ağustos 2027 tarihlidir.") == date(2027, 8, 3)


def test_mutlak_en_ay_adi_gun_once() -> None:
    assert parse_absolute("Delivery is due 15 March 2026.") == date(2026, 3, 15)


def test_mutlak_en_ay_adi_ay_once() -> None:
    assert parse_absolute("Signing on March 15, 2026 in Istanbul.") == date(2026, 3, 15)


def test_gecersiz_takvim_tarihi_none() -> None:
    assert parse_absolute("Teslim 31.02.2026 tarihinde yapılır.") is None


def test_gecersiz_iso_tarihi_none() -> None:
    assert parse_absolute("Teslim 2026-13-45 tarihinde yapılır.") is None


def test_gecersiz_ay_adi_tarihi_none() -> None:
    assert parse_absolute("Teslim 31 Şubat 2026 tarihinde yapılır.") is None


def test_egik_cizgi_bicimi_desteklenmez() -> None:
    assert parse_absolute("Due on 3/15/2026.") is None


def test_tarih_yoksa_none() -> None:
    assert parse_absolute("Bu cümlede tarih yok.") is None


def test_find_absolute_ham_yazimi_dondurur() -> None:
    found = find_absolute("Teslim 15 Mart 2026 tarihinde yapılır.")
    assert found is not None
    assert found[0] == date(2026, 3, 15)
    assert found[1] == "15 Mart 2026"


def test_goreli_tr_gun_anchor_ile() -> None:
    assert parse_relative("Ödeme 30 gün içinde yapılır.", anchor=ANCHOR) == (date(2026, 1, 31), "30 gün içinde")


def test_goreli_tr_ay_anchor_ile() -> None:
    assert parse_relative("Teslim 2 ay içinde yapılır.", anchor=ANCHOR)[0] == date(2026, 3, 1)


def test_goreli_en_gun_anchor_ile() -> None:
    assert parse_relative("Payment within 15 days.", anchor=ANCHOR) == (date(2026, 1, 16), "within 15 days")


def test_goreli_en_hafta_anchor_ile() -> None:
    assert parse_relative("Notice within 2 weeks.", anchor=ANCHOR)[0] == date(2026, 1, 15)


def test_goreli_anchor_yoksa_tahmin_etmez() -> None:
    assert parse_relative("Ödeme 30 gün içinde yapılır.", anchor=None) == (None, "30 gün içinde")


def test_goreli_eslesme_yoksa_bos() -> None:
    assert parse_relative("Teslim hemen yapılır.", anchor=ANCHOR) == (None, None)


def test_ay_sonu_kisaltmasi() -> None:
    assert parse_relative("1 ay içinde", anchor=date(2026, 1, 31))[0] == date(2026, 2, 28)


def test_artik_yil_subat() -> None:
    assert parse_relative("1 ay içinde", anchor=date(2028, 1, 31))[0] == date(2028, 2, 29)


def test_goreli_yil_anchor_ile() -> None:
    assert parse_relative("Süre 1 yıl içinde dolar.", anchor=ANCHOR)[0] == date(2027, 1, 1)


def test_goreli_eslesme_yoksa_bos_ikinci() -> None:
    assert parse_relative("Süre belirsizdir.", anchor=ANCHOR) == (None, None)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("12 ay süreyle", None),
        ("30 gün", None),
        ("içinde", None),
    ],
)
def test_goreli_olmayan_ifadeler(text: str, expected: date | None) -> None:
    assert parse_relative(text, anchor=ANCHOR)[0] == expected
