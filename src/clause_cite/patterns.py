"""Veri güdümlü kalıp kataloğu (TR + EN).

Her kalıp bir düzenli ifade, hedef tür (``kind``), kip (``modality``), sinyal adı ve dil etiketi
taşır. Motor kalıpları çalışma zamanında derler; bir cümlede birden çok kalıp eşleşirse
`extract.py` öncelik kurallarını uygular ve **hepsini** ``signals`` alanına yazar. Kalıplar veri
olarak durur (davranış koda gömülü değildir); ``clause-cite kinds`` komutu kataloğu doğrudan basar.

Dil etiketi ``neutral`` olan kalıplar her iki dilde de uygulanır (ör. para biçimi). ``lang="auto"``
tüm kalıpları, ``lang="tr"``/``lang="en"`` ilgili dili + ``neutral`` kalıpları uygular.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from clause_cite.models import ItemKind, Modality

_FLAGS = re.IGNORECASE | re.UNICODE

_MONEY_REGEX = r"(?:₺|TRY|TL|USD|EUR|lira|\$|€)\s*\d[\d.,]*|\d[\d.,]*\s*(?:₺|TRY|TL|USD|EUR|lira|\$|€)"


class Pattern(BaseModel):
    """Tek bir kalıp kaydı (henüz derlenmemiş hâli)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    signal: str
    pattern: str
    kind: ItemKind
    modality: Modality
    lang: str
    label_tr: str


@dataclass(frozen=True)
class Matcher:
    """Derlenmiş kalıp: çalışma zamanında kullanılan hâli."""

    signal: str
    regex: re.Pattern[str]
    kind: ItemKind
    modality: Modality
    lang: str


PATTERNS: tuple[Pattern, ...] = (
    # --- Türkçe yükümlülük ---------------------------------------------------------------
    Pattern(
        signal="tr_melidir",
        pattern=r"\w*(?:melidir|malıdır)\b",
        kind=ItemKind.OBLIGATION,
        modality=Modality.MUST,
        lang="tr",
        label_tr="-melidir / -malıdır (kesin yükümlülük)",
    ),
    Pattern(
        signal="tr_meli",
        pattern=r"\w*(?:meli|malı)\b",
        kind=ItemKind.OBLIGATION,
        modality=Modality.SHOULD,
        lang="tr",
        label_tr="-meli / -malı (öneri tonlu yükümlülük)",
    ),
    Pattern(
        signal="tr_yukumludur",
        pattern=r"y[üu]k[üu]ml[üu]d[üu]r|y[üu]k[üu]ml[üu]l[üu][ğg]",
        kind=ItemKind.OBLIGATION,
        modality=Modality.MUST,
        lang="tr",
        label_tr="yükümlüdür / yükümlülük",
    ),
    Pattern(
        signal="tr_zorundadir",
        pattern=r"zorunda(?:d[ıi]r)?\b",
        kind=ItemKind.OBLIGATION,
        modality=Modality.MUST,
        lang="tr",
        label_tr="zorundadır / etmek zorunda",
    ),
    Pattern(
        signal="tr_gerekir",
        pattern=r"\bgerekir\b|\bgereklidir\b|\bgerekli\b",
        kind=ItemKind.OBLIGATION,
        modality=Modality.MUST,
        lang="tr",
        label_tr="gerekir / gereklidir",
    ),
    Pattern(
        signal="tr_onerilir",
        pattern=r"önerilir|tavsiye edilir|tavsiye olunur",
        kind=ItemKind.OBLIGATION,
        modality=Modality.SHOULD,
        lang="tr",
        label_tr="önerilir / tavsiye edilir",
    ),
    # --- Türkçe yasak --------------------------------------------------------------------
    Pattern(
        signal="tr_yasaktir",
        pattern=r"yasakt[ıi]r|\byasak\b",
        kind=ItemKind.PROHIBITION,
        modality=Modality.MUST,
        lang="tr",
        label_tr="yasaktır",
    ),
    Pattern(
        signal="tr_mamali",
        pattern=r"\w*(?:mamalıdır|memelidir|mamalı|memeli)\b",
        kind=ItemKind.PROHIBITION,
        modality=Modality.MUST,
        lang="tr",
        label_tr="-mamalıdır / -memelidir",
    ),
    Pattern(
        signal="tr_olumsuz_kip",
        pattern=r"\w+(?:maz|mez)\b",
        kind=ItemKind.PROHIBITION,
        modality=Modality.MUST,
        lang="tr",
        label_tr="-maz / -mez (olumsuz yapılamaz)",
    ),
    Pattern(
        signal="tr_edemez",
        pattern=r"\bedemez\b",
        kind=ItemKind.PROHIBITION,
        modality=Modality.MUST,
        lang="tr",
        label_tr="edemez",
    ),
    Pattern(
        signal="tr_izin_verilmez",
        pattern=r"izin verilmez|izin verilemez|müsaade edilmez|izni yoktur",
        kind=ItemKind.PROHIBITION,
        modality=Modality.MUST,
        lang="tr",
        label_tr="izin verilmez / müsaade edilmez",
    ),
    # --- Türkçe izin / opsiyon -----------------------------------------------------------
    Pattern(
        signal="tr_abilir",
        pattern=r"\w*(?:abilir|ebilir)\b",
        kind=ItemKind.OBLIGATION,
        modality=Modality.MAY,
        lang="tr",
        label_tr="-abilir / -ebilir (izin)",
    ),
    Pattern(
        signal="tr_hakki_vardir",
        pattern=r"hakk[ıi] vard[ıi]r|hak sahibidir",
        kind=ItemKind.OBLIGATION,
        modality=Modality.MAY,
        lang="tr",
        label_tr="hakkı vardır",
    ),
    # --- Türkçe termin -------------------------------------------------------------------
    Pattern(
        signal="tr_en_gec",
        pattern=r"en ge[çc]\b",
        kind=ItemKind.DEADLINE,
        modality=Modality.MAY,
        lang="tr",
        label_tr="en geç",
    ),
    Pattern(
        signal="tr_tarihine_kadar",
        pattern=r"tarihine kadar|tarihten itibaren",
        kind=ItemKind.DEADLINE,
        modality=Modality.MAY,
        lang="tr",
        label_tr="tarihine kadar",
    ),
    Pattern(
        signal="tr_gun_icinde",
        pattern=r"\b\d+\s*(?:gün|hafta|ay|yıl|yil)\s*(?:içinde|içerisinde|zarfında)\b",
        kind=ItemKind.DEADLINE,
        modality=Modality.MAY,
        lang="tr",
        label_tr="N gün/ay içinde",
    ),
    # --- Türkçe belge zorunluluğu --------------------------------------------------------
    Pattern(
        signal="tr_belge_zorunlu",
        pattern=(
            r"sunulması zorunludur|sunulması gerekir|teslim edilmesi gerekir|ibraz edilmesi gerekir"
            r"|sağlanması zorunludur|verilmesi zorunludur|sunulmalıdır"
        ),
        kind=ItemKind.DOCUMENT_REQUIRED,
        modality=Modality.MUST,
        lang="tr",
        label_tr="sunulması zorunludur / teslim edilmesi gerekir",
    ),
    # --- Türkçe tanım --------------------------------------------------------------------
    Pattern(
        signal="tr_tanim",
        pattern=r"\bifade eder\b|\bolarak tanımlanır\b|anlamına gelir|olarak anlaşılır",
        kind=ItemKind.DEFINITION,
        modality=Modality.MAY,
        lang="tr",
        label_tr="ifade eder / olarak tanımlanır",
    ),
    # --- Türkçe belirsizlik --------------------------------------------------------------
    Pattern(
        signal="tr_belirsiz",
        pattern=r"ayrıca belirlenir|taraflarca kararlaştırılır|makul süre|uygun görülen|ihtiyaç halinde",
        kind=ItemKind.AMBIGUOUS,
        modality=Modality.MAY,
        lang="tr",
        label_tr="belirsiz atıf (makul süre, uygun görülen ...)",
    ),
    # --- İngilizce yasak -----------------------------------------------------------------
    Pattern(
        signal="en_shall_not",
        pattern=r"\bshall not\b",
        kind=ItemKind.PROHIBITION,
        modality=Modality.MUST,
        lang="en",
        label_tr="shall not",
    ),
    Pattern(
        signal="en_must_not",
        pattern=r"\bmust not\b",
        kind=ItemKind.PROHIBITION,
        modality=Modality.MUST,
        lang="en",
        label_tr="must not",
    ),
    Pattern(
        signal="en_may_not",
        pattern=r"\bmay not\b",
        kind=ItemKind.PROHIBITION,
        modality=Modality.MUST,
        lang="en",
        label_tr="may not",
    ),
    Pattern(
        signal="en_prohibited",
        pattern=r"\bprohibited\b|\bnot permitted\b|\bnot allowed\b",
        kind=ItemKind.PROHIBITION,
        modality=Modality.MUST,
        lang="en",
        label_tr="prohibited / not permitted",
    ),
    # --- İngilizce yükümlülük ------------------------------------------------------------
    Pattern(
        signal="en_shall",
        pattern=r"\bshall\b",
        kind=ItemKind.OBLIGATION,
        modality=Modality.MUST,
        lang="en",
        label_tr="shall",
    ),
    Pattern(
        signal="en_must",
        pattern=r"\bmust\b",
        kind=ItemKind.OBLIGATION,
        modality=Modality.MUST,
        lang="en",
        label_tr="must",
    ),
    Pattern(
        signal="en_required_to",
        pattern=r"\b(?:is|are) required to\b",
        kind=ItemKind.OBLIGATION,
        modality=Modality.MUST,
        lang="en",
        label_tr="is required to / are required to",
    ),
    Pattern(
        signal="en_should",
        pattern=r"\bshould\b",
        kind=ItemKind.OBLIGATION,
        modality=Modality.SHOULD,
        lang="en",
        label_tr="should",
    ),
    # --- İngilizce izin ------------------------------------------------------------------
    Pattern(
        signal="en_may",
        pattern=r"\bmay\b",
        kind=ItemKind.OBLIGATION,
        modality=Modality.MAY,
        lang="en",
        label_tr="may",
    ),
    Pattern(
        signal="en_entitled_to",
        pattern=r"\b(?:is|are) entitled to\b",
        kind=ItemKind.OBLIGATION,
        modality=Modality.MAY,
        lang="en",
        label_tr="is entitled to / are entitled to",
    ),
    # --- İngilizce belge zorunluluğu -----------------------------------------------------
    Pattern(
        signal="en_belge_zorunlu",
        pattern=r"\bshall (?:provide|submit)\b|\bmust be submitted\b|\bmust (?:provide|submit)\b|\bshall be provided\b",
        kind=ItemKind.DOCUMENT_REQUIRED,
        modality=Modality.MUST,
        lang="en",
        label_tr="shall provide / must be submitted",
    ),
    # --- İngilizce termin ----------------------------------------------------------------
    Pattern(
        signal="en_within",
        pattern=r"\bwithin\s+\d+\s+(?:day|days|week|weeks|month|months|year|years)\b",
        kind=ItemKind.DEADLINE,
        modality=Modality.MAY,
        lang="en",
        label_tr="within N days",
    ),
    Pattern(
        signal="en_no_later_than",
        pattern=r"\bno later than\b",
        kind=ItemKind.DEADLINE,
        modality=Modality.MAY,
        lang="en",
        label_tr="no later than",
    ),
    Pattern(
        signal="en_by_date",
        pattern=r"\bby \d{1,2}[./]\d{1,2}[./]\d{2,4}\b",
        kind=ItemKind.DEADLINE,
        modality=Modality.MAY,
        lang="en",
        label_tr="by <tarih>",
    ),
    # --- İngilizce tanım -----------------------------------------------------------------
    Pattern(
        signal="en_defined",
        pattern=r"\bmeans\b|\bis defined as\b|\brefers to\b",
        kind=ItemKind.DEFINITION,
        modality=Modality.MAY,
        lang="en",
        label_tr="means / is defined as",
    ),
    # --- İngilizce belirsizlik -----------------------------------------------------------
    Pattern(
        signal="en_belirsiz",
        pattern=r"\bas determined\b|\bto be agreed\b|\breasonable time\b|\bas applicable\b|\bfrom time to time\b",
        kind=ItemKind.AMBIGUOUS,
        modality=Modality.MAY,
        lang="en",
        label_tr="belirsiz atıf (as applicable, to be agreed ...)",
    ),
    # --- Para (dil bağımsız) -------------------------------------------------------------
    Pattern(
        signal="money",
        pattern=_MONEY_REGEX,
        kind=ItemKind.MONEY,
        modality=Modality.MAY,
        lang="neutral",
        label_tr="tutar (TL/TRY/USD/EUR, ₺/$/€)",
    ),
)


def compile_patterns(patterns: tuple[Pattern, ...] = PATTERNS) -> tuple[Matcher, ...]:
    """Kalıp kayıtlarını derleyip çalıştırılabilir eşleyicilere çevir."""
    return tuple(
        Matcher(
            signal=item.signal,
            regex=re.compile(item.pattern, _FLAGS),
            kind=item.kind,
            modality=item.modality,
            lang=item.lang,
        )
        for item in patterns
    )


COMPILED: tuple[Matcher, ...] = compile_patterns()


def _lang_matches(pattern_lang: str, lang: str) -> bool:
    """Dil filtresi: ``auto`` hepsini, ``tr``/``en`` ilgili dili + ``neutral`` kalıpları alır."""
    if lang == "auto":
        return True
    return pattern_lang in {lang, "neutral"}


def match_patterns(text: str, *, lang: str = "auto") -> list[Matcher]:
    """Cümlede eşleşen kalıpları (dil filtresi uygulanmış) döndür."""
    if lang not in {"auto", "tr", "en"}:
        msg = f"geçersiz dil: '{lang}' (auto, tr veya en olmalı)"
        raise ValueError(msg)
    return [matcher for matcher in COMPILED if _lang_matches(matcher.lang, lang) and matcher.regex.search(text)]


def patterns_for(kind: ItemKind) -> tuple[Pattern, ...]:
    """Belirli türdeki kalıp kayıtlarını döndür."""
    return tuple(pattern for pattern in PATTERNS if pattern.kind is kind)


def kinds_overview() -> list[tuple[ItemKind, tuple[Pattern, ...]]]:
    """Türleri katalog sırasına göre, ait oldukları kalıplarla birlikte döndür."""
    return [(kind, patterns_for(kind)) for kind in ItemKind]
