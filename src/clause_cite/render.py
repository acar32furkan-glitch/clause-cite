"""Konsol, Markdown, CSV ve GitHub Actions özeti biçiminde çıktı.

Metinler Türkçedir (çıktıyı okuyan kişi hukuk/operasyon ekibidir), sayısal ve teknik alanlar
(``kind``, ``id``, satır numaraları) İngilizce etiketleriyle kalır ki CI kaydı ve JSON sözleşmesi
birebir eşleşsin. Her madde **alıntısını ve atfını** (``dosya:satır-satır``) taşır.
"""

from __future__ import annotations

import csv
import io
from datetime import date
from typing import Any

from clause_cite import __version__
from clause_cite.extract import KIND_PRIORITY
from clause_cite.models import ExtractionResult, Item, ItemKind
from clause_cite.verify import citation_coverage

_CSV_COLUMNS: tuple[str, ...] = (
    "id",
    "kind",
    "modality",
    "document",
    "start_line",
    "end_line",
    "actor",
    "actor_resolved",
    "due_date",
    "due_raw",
    "amount",
    "currency",
    "confidence",
    "needs_review",
    "signals",
    "quote",
)


def _format_item(item: Item) -> list[str]:
    """Tek bir maddeyi insan okur satırlara çevir.

    Tanım maddelerinde kip etiketi gösterilmez: "Hizmet, ... ifade eder" cümlesi opsiyonel ya da
    zorunlu değildir, tanımdır — kip etiketi basmak yanlış anlam kurardı. Kip bilgisi JSON/CSV
    çıktısında korunur (veri kaybı yok), yalnızca insan tarafında gösterilmez.
    """
    label = item.modality.label_tr
    if item.kind is ItemKind.DEFINITION or item.kind is ItemKind.PROHIBITION:
        # Tanımda kip anlamsız; yasakta kip zaten "yapmama"dır ve tür başlığı bunu söyler.
        # "YASAK grubunda ZORUNLU" okuması çelişki gibi görünüyordu → etiket gösterilmez.
        label = "—"
    head = f"  • [{item.id}] {label}"
    if item.actor is not None:
        head += f" · aktör: {item.actor}"
    elif not item.actor_resolved:
        head += " · aktör: (çözülemedi)"
    else:
        head += " · aktör: (metinde belirtilmemiş)"
    if item.due_date is not None:
        head += f" · termin: {item.due_date.isoformat()}"
    elif item.due_raw is not None:
        head += f" · termin: {item.due_raw} (anchor yok)"
    if item.amount is not None:
        head += f" · tutar: {item.amount:.2f} {item.currency}"
    head += f" · güven: {item.confidence.label_tr}"
    if item.needs_review:
        head += " · İNCELEME GEREKİYOR"
    lines = [head, f"      atıf : {item.citation}", f'      alıntı: "{item.quote}"']
    if item.signals:
        lines.append(f"      sinyal: {', '.join(item.signals)}")
    return lines


def render_text(result: ExtractionResult, *, max_items: int | None = None) -> str:
    """Tür bazlı gruplanmış Türkçe konsol çıktısı."""
    lines = ["ÇIKARILAN AKSİYON MADDELERİ", ""]
    lines.append(
        f"  belge: {len(result.documents)} · cümle: {result.sentences} · madde: {len(result.items)}"
        f" · çözülemeyen: {result.unresolved_count()} · aktörsüz: {result.actorless_count()}"
    )
    if "eliminated" in result.stats:
        lines.append(f"  --strict ile elenen madde: {result.eliminated_count()}")
    lines.append("")
    shown = result.items if max_items is None else result.items[: max(0, max_items)]
    if not result.items:
        lines.append("Madde bulunamadı.")
    for kind in KIND_PRIORITY:
        group = [item for item in shown if item.kind is kind]
        if not group:
            continue
        lines.append(f"{kind.label_tr} ({kind.value}) — {len(group)} madde")
        for item in group:
            lines.extend(_format_item(item))
        lines.append("")
    hidden = len(result.items) - len(shown)
    if hidden > 0:
        lines.append(f"  … {hidden} madde daha var (--max-items ile sınırı artırın).")
    return "\n".join(lines).rstrip() + "\n"


def render_markdown(result: ExtractionResult) -> str:
    """Maddelerin Markdown tablo özeti."""
    lines = [
        "### Kanıtlı aksiyon maddeleri",
        "",
        f"- belge: {len(result.documents)} · cümle: {result.sentences} · madde: {len(result.items)}",
        (
            f"- çözülemeyen: {result.unresolved_count()} · aktörsüz: {result.actorless_count()}"
            f" · alıntı kapsamı: %{citation_coverage(result) * 100:.0f}"
        ),
        "",
        "| Kimlik | Tür | Kip | Taraf | Termin | Atıf |",
        "|--------|-----|-----|-------|--------|------|",
    ]
    counts = result.by_kind()
    for kind in KIND_PRIORITY:
        if counts[kind] == 0:
            continue
        lines.append(f"| **{kind.label_tr}** | {kind.value} | — | — | — | {counts[kind]} madde |")
        for item in result.items:
            if item.kind is not kind:
                continue
            actor = item.actor or ("" if item.actor_resolved else "çözülemedi")
            due = item.due_date.isoformat() if item.due_date is not None else (item.due_raw or "")
            lines.append(
                f"| {item.id} | {item.kind.value} | {item.modality.label_tr} | {actor} | {due} | `{item.citation}` |"
            )
    lines.extend(["", "<sub>clause-cite · deterministik çıkarım, LLM çağrısı yok</sub>"])
    return "\n".join(lines)


def render_csv(result: ExtractionResult) -> str:
    """Maddeleri CSV olarak ver (başlık satırı İngilizce alan adlarıyla)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(_CSV_COLUMNS)
    for item in result.items:
        writer.writerow(
            [
                item.id,
                item.kind.value,
                item.modality.value,
                item.document,
                item.start_line,
                item.end_line,
                item.actor or "",
                item.actor_resolved,
                item.due_date.isoformat() if item.due_date is not None else "",
                item.due_raw or "",
                f"{item.amount:.2f}" if item.amount is not None else "",
                item.currency or "",
                item.confidence.value,
                item.needs_review,
                "|".join(item.signals),
                item.quote,
            ]
        )
    return buffer.getvalue()


def render_github_summary(result: ExtractionResult) -> str:
    """GitHub Actions iş özeti için Markdown bloğu."""
    return render_markdown(result)


def render_json_payload(result: ExtractionResult, *, anchor: date | None = None) -> dict[str, Any]:
    """JSON sözleşmesi: sürüm, anchor, maddeler ve özet sayaçlar."""
    return {
        "version": __version__,
        "anchor": anchor.isoformat() if anchor is not None else None,
        "documents": list(result.documents),
        "sentences": result.sentences,
        "item_count": len(result.items),
        "unresolved": result.unresolved_count(),
        "eliminated": result.eliminated_count(),
        "coverage": round(citation_coverage(result), 4),
        "counts": {kind.value: count for kind, count in result.by_kind().items()},
        "items": [item.model_dump(mode="json") for item in result.items],
    }
