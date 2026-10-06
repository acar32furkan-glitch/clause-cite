"""Deterministik tarih çözümleme: mutlak tarihler ve göreli terminler.

İki kural esastır:

* **Uydurma yok.** Göreli bir termin (``30 gün içinde``) yalnızca bir ``anchor`` verildiğinde
  somut tarihe çevrilir; anchor yoksa tarih ``None`` döner, ham metin (``due_raw``) korunur ve madde
  ``needs_review`` ile işaretlenir.
* **Belirsiz biçim kabul edilmez.** ``3/15/2026`` gibi ay/gün/yıl sırası karışık yazımlar
  desteklenmez; sessizce yanlış yorumlamak yerine ``None`` döner.
"""

from __future__ import annotations

import calendar
import re
from datetime import date, timedelta

_TR_MONTHS: dict[str, int] = {
    "ocak": 1,
    "şubat": 2,
    "mart": 3,
    "nisan": 4,
    "mayıs": 5,
    "haziran": 6,
    "temmuz": 7,
    "ağustos": 8,
    "eylül": 9,
    "ekim": 10,
    "kasım": 11,
    "aralık": 12,
}
_EN_MONTHS: dict[str, int] = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sept": 9,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}
_MONTHS: dict[str, int] = {**_TR_MONTHS, **_EN_MONTHS}
_MONTH_ALT = "|".join(sorted(_MONTHS, key=len, reverse=True))

_ISO = re.compile(r"\b(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\b")
_DOTTED = re.compile(r"\b(?P<day>\d{1,2})\.(?P<month>\d{1,2})\.(?P<year>\d{4})\b")
_DAY_MONTH_YEAR = re.compile(
    rf"\b(?P<day>\d{{1,2}})\s+(?P<month>{_MONTH_ALT})\.?\s+(?P<year>\d{{4}})\b",
    re.IGNORECASE,
)
_MONTH_DAY_YEAR = re.compile(
    rf"\b(?P<month>{_MONTH_ALT})\.?\s+(?P<day>\d{{1,2}}),?\s+(?P<year>\d{{4}})\b",
    re.IGNORECASE,
)

_TR_RELATIVE = re.compile(
    r"(?P<num>\d+)\s*(?P<unit>gün|hafta|ay|yıl|yil)\s*(?:içinde|içerisinde|zarfında)",
    re.IGNORECASE,
)
_EN_RELATIVE = re.compile(
    r"\bwithin\s+(?P<num>\d+)\s+(?P<unit>day|days|week|weeks|month|months|year|years)\b",
    re.IGNORECASE,
)

_TR_UNITS: dict[str, str] = {"gün": "day", "hafta": "week", "ay": "month", "yıl": "year", "yil": "year"}


def _build(year: int, month: int, day: int) -> date | None:
    """Geçerli bir tarih kur; takvimde yoksa ``None`` döndür (uydurma)."""
    try:
        return date(year, month, day)
    except ValueError:
        return None


def find_absolute(text: str) -> tuple[date, str] | None:
    """Metindeki ilk mutlak tarihi ve kaynakta geçtiği ham yazımını döndür.

    Desteklenen biçimler: ``2026-03-15``, ``15.03.2026``, ``15 Mart 2026``, ``March 15, 2026``.
    """
    iso = _ISO.search(text)
    if iso is not None:
        value = _build(int(iso["year"]), int(iso["month"]), int(iso["day"]))
        if value is not None:
            return value, iso.group(0)
    dotted = _DOTTED.search(text)
    if dotted is not None:
        value = _build(int(dotted["year"]), int(dotted["month"]), int(dotted["day"]))
        if value is not None:
            return value, dotted.group(0)
    for regex in (_DAY_MONTH_YEAR, _MONTH_DAY_YEAR):
        match = regex.search(text)
        if match is None:
            continue
        month = _MONTHS[match["month"].lower().rstrip(".")]
        value = _build(int(match["year"]), month, int(match["day"]))
        if value is not None:
            return value, match.group(0)
    return None


def parse_absolute(text: str) -> date | None:
    """Metindeki ilk mutlak tarihi döndür; yoksa ya da belirsizse ``None``."""
    found = find_absolute(text)
    return found[0] if found is not None else None


def _add_months(value: date, months: int) -> date:
    """Ay ekle; hedef ay kısa ise günü ayın son gününe kısar (ör. 31 Ocak + 1 ay → 28/29 Şubat)."""
    index = value.month - 1 + months
    year = value.year + index // 12
    month = index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _normalize_unit(raw: str) -> str:
    """Ham birim adını ``day``/``week``/``month``/``year`` değerine indirge."""
    key = raw.lower()
    if key in _TR_UNITS:
        return _TR_UNITS[key]
    return key.rstrip("s")


def _advance(anchor: date, count: int, unit: str) -> date:
    """Anchor tarihini ``count`` birim ileri taşı."""
    if unit == "day":
        return anchor + timedelta(days=count)
    if unit == "week":
        return anchor + timedelta(weeks=count)
    if unit == "month":
        return _add_months(anchor, count)
    return _add_months(anchor, 12 * count)


def parse_relative(text: str, *, anchor: date | None) -> tuple[date | None, str | None]:
    """Göreli bir termini çöz: ``(tarih, ham_metin)`` döndür.

    Anchor yoksa tarih ``None`` olur ve ham metin korunur; motor asla tahmin etmez.
    """
    for regex in (_TR_RELATIVE, _EN_RELATIVE):
        match = regex.search(text)
        if match is None:
            continue
        raw = match.group(0).strip()
        if anchor is None:
            return None, raw
        return _advance(anchor, int(match["num"]), _normalize_unit(match["unit"])), raw
    return None, None
