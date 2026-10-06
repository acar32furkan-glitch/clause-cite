"""`clause-cite extract` çıktısını SVG "terminal kaydı" olarak üretir.

README'de ekran görüntüsü yerine gerçek çıktının görseli durur: betik örnek belgeleri çıkarır,
alıntı invaryantını doğrular ve metni renkli bir SVG'ye çevirir. Çıktı değiştiğinde görsel de
kendiliğinden güncellenir (`make demo-svg`).

Determinizm: zaman ``ANCHOR`` (2026-01-01) sabitinden gelir, ağ çağrısı ve rastgelelik yoktur; bu
yüzden betik her koşuda aynı SVG'yi üretir.
"""

from __future__ import annotations

import html
import sys
from datetime import date
from pathlib import Path

from clause_cite.extract import extract
from clause_cite.render import render_text
from clause_cite.text import load_document
from clause_cite.verify import verify_citations

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "examples" / "data"
OUTPUT = PROJECT / "docs" / "assets" / "demo.svg"

ANCHOR = date(2026, 1, 1)
MAX_ITEMS = 12

CHAR_WIDTH = 7.62
LINE_HEIGHT = 19
PADDING_X = 22
PADDING_TOP = 62
MAX_CHARS = 112
MIN_WRAP_CUT = 20

BACKGROUND = "#0b1120"
CHROME = "#1e293b"
TEXT = "#e2e8f0"
DIM = "#94a3b8"
REVIEW_COLOR = "#fbbf24"
OK_COLOR = "#4ade80"
KIND_COLORS = {
    "YASAK": "#f87171",
    "BELGE_ZORUNLU": "#c4b5fd",
    "YÜKÜMLÜLÜK": "#7dd3fc",
    "TERMİN": "#38bdf8",
    "PARA": "#4ade80",
    "TANIM": "#e2e8f0",
    "BELİRSİZ": "#fbbf24",
}


def wrap(lines: list[str], *, width: int = MAX_CHARS) -> list[str]:
    """Uzun satırları görselde taşmayacak biçimde böl."""
    wrapped: list[str] = []
    for line in lines:
        if len(line) <= width:
            wrapped.append(line)
            continue
        indent = " " * (line.index(":") + 2 if ":" in line[:16] else 7)
        current = line
        while len(current) > width:
            cut = current.rfind(" ", 0, width)
            cut = cut if cut > MIN_WRAP_CUT else width
            wrapped.append(current[:cut])
            current = indent + current[cut:].lstrip()
        wrapped.append(current)
    return wrapped


def color_for(line: str) -> str:
    """Satırın rengini içeriğe göre seç (tür başlığı, inceleme uyarısı, doğrulama satırı)."""
    if "İNCELEME GEREKİYOR" in line:
        return REVIEW_COLOR
    if "alıntı doğrulaması" in line:
        return OK_COLOR
    stripped = line.strip()
    for marker, color in KIND_COLORS.items():
        if stripped.startswith(f"{marker} ("):
            return color
    if stripped.startswith("•"):
        return TEXT
    if line.startswith(("  belge:", "      ", "  …")) or not stripped:
        return DIM
    return TEXT


def build_svg(lines: list[str], *, title: str) -> str:
    """Satırları koyu, terminal görünümlü bir SVG belgesine çevir."""
    lines = [line[:MAX_CHARS] for line in lines]
    width = int(max(len(line) for line in lines) * CHAR_WIDTH) + PADDING_X * 2
    height = PADDING_TOP + len(lines) * LINE_HEIGHT + 26
    rows: list[str] = []
    for index, line in enumerate(lines):
        y = PADDING_TOP + index * LINE_HEIGHT
        color = color_for(line)
        content = html.escape(line, quote=False)
        rows.append(
            f'<text x="{PADDING_X}" y="{y}" fill="{color}" font-family="ui-monospace, SFMono-Regular, '
            f'Menlo, Consolas, monospace" font-size="13.5" xml:space="preserve">{content}</text>'
        )
    return "\n".join(
        [
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
                f'viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">'
            ),
            f'  <rect width="{width}" height="{height}" rx="10" fill="{BACKGROUND}"/>',
            f'  <rect width="{width}" height="38" rx="10" fill="{CHROME}"/>',
            f'  <rect y="28" width="{width}" height="10" fill="{CHROME}"/>',
            '  <circle cx="20" cy="19" r="6" fill="#f87171"/>',
            '  <circle cx="40" cy="19" r="6" fill="#fbbf24"/>',
            '  <circle cx="60" cy="19" r="6" fill="#4ade80"/>',
            (
                f'  <text x="{PADDING_X + 60}" y="24" fill="{DIM}" font-family="ui-sans-serif, system-ui, '
                f'sans-serif" font-size="12.5">{html.escape(title)}</text>'
            ),
            *("  " + row for row in rows),
            "</svg>",
        ]
    )


def main() -> int:
    """Örnek belgeler üzerinde çıkarım yap, alıntıyı doğrula ve SVG'yi yaz."""
    documents = [load_document(path) for path in sorted(DATA.glob("*.txt"))]
    result = extract(documents, anchor=ANCHOR)
    violations, stats = verify_citations(result)
    text = render_text(result, max_items=MAX_ITEMS)
    if violations:
        footer = f"İHLAL: {len(violations)} alıntı doğrulanamadı"
    else:
        footer = (
            f"alıntı doğrulaması: {stats.cited}/{stats.items} madde doğrulandı (kapsam %{stats.coverage * 100:.0f})"
        )
    lines = wrap([*text.splitlines(), "", footer])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_svg(lines, title="clause-cite extract — örnek belgeler"), encoding="utf-8", newline="\n")
    sys.stdout.write(f"yazıldı: {OUTPUT} ({len(lines)} satır, {len(result.items)} madde)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
