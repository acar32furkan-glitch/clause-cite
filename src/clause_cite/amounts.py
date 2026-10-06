"""Deterministik tutar çözümleme: TR (``1.234,56 TL``) ve EN (``USD 5,000``) biçimleri.

Tutarlar `Decimal` üzerinden işlenir; float'a asla düşülmez ve iki ondalığa yuvarlama
``ROUND_HALF_UP`` ile yapılır. Para birimi kaynakta geçtiği hâliyle (kod ya da sembol) korunur;
tutardan bağımsız sayılar (ör. ``30``) tutar sayılmaz — bir para birimi belirteci zorunludur.
"""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

_CURRENCY = r"(?:₺|TRY|TL|USD|EUR|lira|\$|€)"
_MONEY = re.compile(
    rf"(?P<cur_first>{_CURRENCY})\s*(?P<num_first>\d[\d.,]*)|(?P<num_last>\d[\d.,]*)\s*(?P<cur_last>{_CURRENCY})",
    re.IGNORECASE,
)

_TR_CURRENCIES: frozenset[str] = frozenset({"TL", "TRY", "₺", "LIRA"})
_CENT = Decimal("0.01")


def normalize_currency(raw: str) -> str:
    """Para birimi kodunu büyük harfe çevir; sembolleri olduğu gibi bırak."""
    return raw.upper() if raw.isalpha() else raw


def _to_decimal(raw_number: str, currency: str) -> Decimal | None:
    """Ham sayı metnini para birimine göre ``Decimal``'a çevir (binlik/ondalık ayırıcı ayrımı).

    Para birimi TR ise binlik ayırıcı nokta, ondalık ayırıcı virgüldür (``1.234,56``); diğer tüm
    para birimleri için ondalık ayırıcı noktadır (``1,234.56``). Ayırıcı düzeni bozuk girdi
    (ör. ``1,2,3``) sessizce yorumlanmaz, ``None`` döner.
    """
    raw = raw_number.rstrip(".,")
    cleaned = raw.replace(".", "").replace(",", ".") if currency in _TR_CURRENCIES else raw.replace(",", "")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def parse_amount(text: str) -> tuple[Decimal, str] | None:
    """Metindeki ilk tutarı ``(değer, para birimi)`` olarak döndür; yoksa ``None``.

    Değer iki ondalığa ``ROUND_HALF_UP`` ile yuvarlanır; para birimi kaynakta geçtiği hâliyle
    döner (``TL``, ``USD``, ``₺``, ``$`` ...).
    """
    match = _MONEY.search(text)
    if match is None:
        return None
    if match["cur_first"] is not None:
        raw_currency, raw_number = match["cur_first"], match["num_first"]
    else:
        raw_currency, raw_number = match["cur_last"], match["num_last"]
    currency = normalize_currency(raw_currency)
    value = _to_decimal(raw_number, currency)
    if value is None:
        return None
    return value.quantize(_CENT, rounding=ROUND_HALF_UP), currency
