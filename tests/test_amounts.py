"""Tutar çözümleme: TR/EN biçimleri, semboller, kodlar ve ROUND_HALF_UP yuvarlama."""

from __future__ import annotations

from decimal import Decimal

import pytest

from clause_cite.amounts import normalize_currency, parse_amount


def value(text: str) -> Decimal:
    """Metindeki tutarın değerini döndür (yoksa hata)."""
    found = parse_amount(text)
    assert found is not None
    return found[0]


def currency(text: str) -> str:
    """Metindeki tutarın para birimini döndür (yoksa hata)."""
    found = parse_amount(text)
    assert found is not None
    return found[1]


def test_tr_bicimi_binlik_nokta_ondalik_virgul() -> None:
    assert parse_amount("Gecikme cezası 1.234,56 TL'dir.") == (Decimal("1234.56"), "TL")


def test_tr_bicimi_kisa() -> None:
    assert parse_amount("Ücret 500,50 TL olarak belirlenir.") == (Decimal("500.50"), "TL")


def test_tr_bicimi_try_kodu() -> None:
    assert currency("Ödeme 2.000,00 TRY yapılır.") == "TRY"


def test_tl_sembolu() -> None:
    assert parse_amount("Tutar ₺750,25 olarak ödenir.") == (Decimal("750.25"), "₺")


def test_en_bicimi_binlik_virgul_ondalik_nokta() -> None:
    assert parse_amount("Late payment penalty is USD 5,000.") == (Decimal("5000.00"), "USD")


def test_en_bicimi_dolar_sembolu() -> None:
    assert parse_amount("Fee of $1,234.56 applies.") == (Decimal("1234.56"), "$")


def test_euro_sembolu_onek() -> None:
    assert parse_amount("Ceza €500 tutarında uygulanır.") == (Decimal("500.00"), "€")


def test_euro_kodu() -> None:
    assert currency("The price is EUR 1,000.") == "EUR"


def test_yuvarlama_half_up_yukari() -> None:
    assert value("Tutar 1.234,565 TL'dir.") == Decimal("1234.57")


def test_yuvarlama_half_up_asagi() -> None:
    assert value("Tutar 1.234,564 TL'dir.") == Decimal("1234.56")


def test_yuvarlama_float_kullanmaz() -> None:
    result = value("Tutar 0,005 TL'dir.")
    assert result == Decimal("0.01")
    assert isinstance(result, Decimal)


def test_para_birimi_yoksa_none() -> None:
    assert parse_amount("Ödeme 30 gün içinde yapılır.") is None


def test_bozuk_ayirici_sessizce_yorumlanmaz() -> None:
    assert parse_amount("Tutar 1,2,3 TL'dir.") is None


def test_tutar_yoksa_none() -> None:
    assert parse_amount("Bu cümlede tutar geçmez.") is None


def test_para_birimi_buyuk_harfe_cevrilir() -> None:
    assert normalize_currency("tl") == "TL"
    assert normalize_currency("usd") == "USD"
    assert normalize_currency("₺") == "₺"


@pytest.mark.parametrize(
    ("text", "expected_value", "expected_currency"),
    [
        ("1.234,56 TL", "1234.56", "TL"),
        ("USD 5,000", "5000.00", "USD"),
        ("€500", "500.00", "€"),
        ("$1,234.56", "1234.56", "$"),
        ("250.000,00 TL", "250000.00", "TL"),
    ],
)
def test_bicim_tablosu(text: str, expected_value: str, expected_currency: str) -> None:
    assert parse_amount(text) == (Decimal(expected_value), expected_currency)
