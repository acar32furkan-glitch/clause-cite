"""Deterministik çıkarım motoru.

Akış: belge → cümleler → kalıp eşleşmeleri → tür/kip kararı → aktör, tarih ve tutar zenginleştirme
→ güven skoru → (isteğe bağlı) ``strict`` eleme. Motor saftır: ağ yok, LLM yok, "şimdi" dışarıdan
``anchor`` olarak enjekte edilir; aynı girdi her zaman aynı maddeleri ve aynı kimlikleri üretir.

Karar kuralları:

* **Tür önceliği** (aynı cümlede birden çok tür eşleşirse): yasak > belge zorunluluğu > yükümlülük >
  termin > para > tanım > belirsiz.
* **Kip önceliği**: ``must`` > ``should`` > ``may``. Kip asla birleştirilmez; eşleşen **tüm** kalıp
  sinyalleri ``signals`` alanına yazılır.
* **Güven**: bağımsız sinyal sayısı + netleşen aktör/tarih/tutar arttıkça yükselir; çözülemeyen
  göreli tarih ve çözülemeyen taraf güveni düşürür.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from clause_cite.amounts import parse_amount
from clause_cite.dates import find_absolute, parse_relative
from clause_cite.models import Confidence, Document, ExtractionResult, Item, ItemKind, Modality
from clause_cite.patterns import Matcher, match_patterns
from clause_cite.text import split_sentences

KIND_PRIORITY: tuple[ItemKind, ...] = (
    ItemKind.PROHIBITION,
    ItemKind.DOCUMENT_REQUIRED,
    ItemKind.OBLIGATION,
    ItemKind.DEADLINE,
    ItemKind.MONEY,
    ItemKind.DEFINITION,
    ItemKind.AMBIGUOUS,
)

MODALITY_PRIORITY: tuple[Modality, ...] = (Modality.MUST, Modality.SHOULD, Modality.MAY)

_ACTORS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Satıcı", re.compile(r"\b[Ss]at[ıi]c[ıi]\b")),
    ("Alıcı", re.compile(r"\b[Aa]l[ıi]c[ıi]\b")),
    ("Yüklenici", re.compile(r"\b[Yy][üu]klenici\b")),
    ("Tedarikçi", re.compile(r"\b[Tt]edarik[çc]i\b")),
    ("Hizmet Sunan", re.compile(r"\b[Hh]izmet [Ss]unan\b")),
    ("Müşteri", re.compile(r"\b[Mm][üu][şs]teri\b")),
    ("İdare", re.compile(r"\b[İI]dare\b")),
    ("Seller", re.compile(r"\b[Ss]eller\b")),
    ("Buyer", re.compile(r"\b[Bb]uyer\b")),
    ("Contractor", re.compile(r"\b[Cc]ontractor\b")),
    ("Supplier", re.compile(r"\b[Ss]upplier\b")),
    ("Provider", re.compile(r"\b[Pp]rovider\b")),
    ("Customer", re.compile(r"\b[Cc]ustomer\b")),
)

_UNRESOLVED_ACTOR = re.compile(
    r"\bilgili taraf\b|\başağıda belirtilen taraf\b|\büçüncü bir taraf\b|"
    r"\bthe relevant party\b|\bthe affected party\b|\ba third party\b",
    re.IGNORECASE,
)

_WHITESPACE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    """Beyaz boşluğu tek boşluğa indirge."""
    return _WHITESPACE.sub(" ", text).strip()


def pick_kind(matches: Sequence[Matcher]) -> ItemKind:
    """Eşleşen kalıplar arasından tür önceliğine göre türü seç."""
    present = {matcher.kind for matcher in matches}
    for kind in KIND_PRIORITY:
        if kind in present:
            return kind
    return ItemKind.AMBIGUOUS


def pick_modality(matches: Sequence[Matcher]) -> Modality:
    """Eşleşen kalıplar arasından kip önceliğine göre kipi seç (must > should > may)."""
    present = {matcher.modality for matcher in matches}
    for modality in MODALITY_PRIORITY:
        if modality in present:
            return modality
    return Modality.MAY


def detect_actor(text: str) -> tuple[str | None, bool]:
    """Cümledeki tarafı tanı; çözülemeyen taraf referansını ``(None, False)`` ile işaretle."""
    for title, regex in _ACTORS:
        if regex.search(text):
            return title, True
    if _UNRESOLVED_ACTOR.search(text):
        return None, False
    return None, True


def resolve_date(text: str, *, anchor: date | None) -> tuple[date | None, str | None]:
    """Cümledeki termini çöz: önce mutlak tarih, yoksa anchor'a bağlı göreli termin."""
    absolute = find_absolute(text)
    if absolute is not None:
        return absolute[0], absolute[1]
    return parse_relative(text, anchor=anchor)


def resolve_amount(text: str) -> tuple[Decimal | None, str | None]:
    """Cümledeki tutarı çöz; tutar yoksa ``(None, None)``."""
    found = parse_amount(text)
    return found if found is not None else (None, None)


def score_confidence(
    *,
    signal_count: int,
    actor: str | None,
    actor_resolved: bool,
    due_date: date | None,
    due_raw: str | None,
    amount: Decimal | None,
) -> Confidence:
    """Bağımsız sinyal, aktör, tarih ve tutar netliğinden güven düzeyi üret."""
    score = signal_count
    if actor is not None and actor_resolved:
        score += 1
    if due_date is not None or amount is not None:
        score += 1
    if due_raw is not None and due_date is None:
        score -= 1
    if not actor_resolved:
        score -= 1
    if score >= 3:
        return Confidence.HIGH
    if score >= 2:
        return Confidence.MEDIUM
    return Confidence.LOW


def extract(
    result_documents: Sequence[Document],
    *,
    anchor: date | None = None,
    lang: str = "auto",
    strict: bool = False,
) -> ExtractionResult:
    """Belgeleri kanıtlı aksiyon maddelerine çevir (saf fonksiyon).

    Args:
        result_documents: Taranacak belgeler (sıra, madde kimliklerindeki ``DOC<n>`` önekini belirler).
        anchor: Göreli terminlerin çözüleceği referans tarihi; ``None`` ise göreli tarih çözülmez.
        lang: ``auto`` | ``tr`` | ``en`` — kalıp kataloğuna uygulanan dil filtresi.
        strict: Yalnızca ``HIGH`` güvenli maddeleri döndür; elenenler ``stats`` içinde sayılır.
    """
    items: list[Item] = []
    seen: set[tuple[str, int, str]] = set()
    sentences_total = 0
    eliminated = 0
    for document_index, document in enumerate(result_documents, start=1):
        prefix = f"DOC{document_index}"
        sequence = 0
        for sentence in split_sentences(document):
            sentences_total += 1
            matches = match_patterns(sentence.text, lang=lang)
            if not matches:
                continue
            key = (document.name, sentence.start_line, sentence.text)
            if key in seen:
                continue
            seen.add(key)
            signals = tuple(dict.fromkeys(matcher.signal for matcher in matches))
            kind = pick_kind(matches)
            modality = pick_modality(matches)
            actor, actor_resolved = detect_actor(sentence.text)
            due_date, due_raw = resolve_date(sentence.text, anchor=anchor)
            amount, currency = resolve_amount(sentence.text)
            confidence = score_confidence(
                signal_count=len(signals),
                actor=actor,
                actor_resolved=actor_resolved,
                due_date=due_date,
                due_raw=due_raw,
                amount=amount,
            )
            unresolved = (not actor_resolved) or (due_raw is not None and due_date is None)
            if strict and confidence is not Confidence.HIGH:
                eliminated += 1
                continue
            sequence += 1
            items.append(
                Item(
                    id=f"{prefix}-{sequence:04d}",
                    kind=kind,
                    modality=modality,
                    text=_normalize(sentence.text),
                    quote=sentence.text,
                    document=document.name,
                    start_line=sentence.start_line,
                    end_line=sentence.end_line,
                    actor=actor,
                    actor_resolved=actor_resolved,
                    due_date=due_date,
                    due_raw=due_raw,
                    amount=amount,
                    currency=currency,
                    confidence=confidence,
                    needs_review=unresolved or confidence is Confidence.LOW,
                    signals=signals,
                )
            )
    stats: dict[str, int] = {"eliminated": eliminated} if strict else {}
    return ExtractionResult(
        items=tuple(items),
        documents=tuple(document.name for document in result_documents),
        sentences=sentences_total,
        sources=tuple(result_documents),
        stats=stats,
    )
