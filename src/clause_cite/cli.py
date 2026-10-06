"""Komut satırı arayüzü.

::

    clause-cite extract <dosya...> [--anchor YYYY-MM-DD] [--json] [--report out.json]
                                   [--csv out.csv] [--fail-on-unresolved] [--strict]
                                   [--max-items N] [--github-summary] [--lang auto|tr|en]
    clause-cite verify <dosya...>
    clause-cite eval examples/golden
    clause-cite kinds

Çıkış kodları: ``0`` temiz · ``1`` politika/invariyant düştü · ``2`` girdi hatası.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from clause_cite import __version__
from clause_cite.extract import extract
from clause_cite.golden import render_golden_text, run_golden
from clause_cite.models import Document
from clause_cite.patterns import PATTERNS, kinds_overview
from clause_cite.render import render_csv, render_github_summary, render_json_payload, render_text
from clause_cite.text import load_document
from clause_cite.verify import verify_citations

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_INPUT_ERROR = 2


def build_parser() -> argparse.ArgumentParser:
    """Argparse ağacını kur (tek parser, her görev için alt komut)."""
    parser = argparse.ArgumentParser(
        prog="clause-cite",
        description="Sözleşme/yönetmelik/şartname metinlerini kanıtlı aksiyon maddelerine çevirir.",
    )
    parser.add_argument("--version", action="version", version=f"clause-cite {__version__}")
    sub = parser.add_subparsers(dest="command")

    extract_parser = sub.add_parser("extract", help="Belgelerden kanıtlı aksiyon maddeleri çıkar.")
    extract_parser.add_argument("documents", nargs="+", type=Path, help="Girdi belgeleri (.txt/.md).")
    extract_parser.add_argument("--anchor", default=None, help="Göreli terminler için referans tarihi (YYYY-MM-DD).")
    extract_parser.add_argument("--json", action="store_true", dest="as_json", help="Sonucu JSON olarak ver.")
    extract_parser.add_argument("--report", type=Path, default=None, help="JSON raporunu bu dosyaya da yaz.")
    extract_parser.add_argument("--csv", type=Path, default=None, help="Maddeleri CSV olarak bu dosyaya yaz.")
    extract_parser.add_argument(
        "--fail-on-unresolved",
        action="store_true",
        help="Çözülemeyen (taraf/tarih) madde varsa çıkış kodu 1 ver.",
    )
    extract_parser.add_argument("--strict", action="store_true", help="Yalnızca yüksek güvenli maddeleri döndür.")
    extract_parser.add_argument("--max-items", type=int, default=None, help="Konsolda gösterilecek en fazla madde.")
    extract_parser.add_argument(
        "--github-summary",
        action="store_true",
        help="Markdown özetini $GITHUB_STEP_SUMMARY dosyasına ekle (Actions iş özeti).",
    )
    extract_parser.add_argument("--lang", choices=("auto", "tr", "en"), default="auto", help="Kalıp dili filtresi.")

    verify_parser = sub.add_parser("verify", help="Alıntı invaryantını denetle (quote ↔ satır aralığı).")
    verify_parser.add_argument("documents", nargs="+", type=Path, help="Girdi belgeleri (.txt/.md).")

    evaluation = sub.add_parser("eval", help="Altın set regresyon vakalarını çalıştır.")
    evaluation.add_argument("golden", type=Path, help="golden.json içeren klasör.")
    evaluation.add_argument("--json", action="store_true", dest="as_json", help="Sonucu JSON olarak ver.")

    sub.add_parser("kinds", help="Madde türlerini ve örnek kalıpları göster.")
    return parser


def _load_documents(paths: Sequence[Path]) -> list[Document]:
    """Belgeleri yükle; eksik/boş belge hataları çağırana (dolayısıyla çıkış kodu 2'ye) gider."""
    return [load_document(path) for path in paths]


def _parse_anchor(value: str | None) -> date | None:
    """``YYYY-MM-DD`` biçimindeki anchor'ı tarihe çevir; geçersizse girdi hatası."""
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        msg = f"geçersiz anchor: '{value}' (YYYY-MM-DD bekleniyor)"
        raise ValueError(msg) from exc


def _write_github_summary(content: str) -> None:
    """İş özetini ``$GITHUB_STEP_SUMMARY`` dosyasına ekle (tanımlı değilse uyar)."""
    target = os.environ.get("GITHUB_STEP_SUMMARY", "").strip()
    if not target:
        print("uyarı: GITHUB_STEP_SUMMARY tanımlı değil, iş özeti yazılmadı.", file=sys.stderr)
        return
    with Path(target).open("a", encoding="utf-8") as handle:
        handle.write(content + "\n")


def cmd_extract(args: argparse.Namespace) -> int:
    """Belgelerden maddeleri çıkar, istenen biçimlerde yaz ve politikayı uygula."""
    documents = _load_documents(args.documents)
    anchor = _parse_anchor(args.anchor)
    result = extract(documents, anchor=anchor, lang=args.lang, strict=args.strict)
    payload = render_json_payload(result, anchor=anchor)

    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.csv is not None:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        args.csv.write_text(render_csv(result), encoding="utf-8")
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(result, max_items=args.max_items))
    if args.github_summary:
        _write_github_summary(render_github_summary(result))

    if args.fail_on_unresolved and result.unresolved_count() > 0:
        print(
            f"politika: {result.unresolved_count()} madde çözülemedi (--fail-on-unresolved).",
            file=sys.stderr,
        )
        return EXIT_FAILED
    return EXIT_OK


def cmd_verify(args: argparse.Namespace) -> int:
    """Her maddenin alıntısını kaynak satır aralığına karşı doğrula."""
    documents = _load_documents(args.documents)
    result = extract(documents)
    violations, stats = verify_citations(result)
    if violations:
        for violation in violations:
            print(f"İHLAL: {violation}", file=sys.stderr)
        print(f"alıntı doğrulaması: {stats.violations} ihlal / {stats.items} madde", file=sys.stderr)
        return EXIT_FAILED
    print(f"alıntı doğrulaması: {stats.cited}/{stats.items} madde doğrulandı (kapsam %{stats.coverage * 100:.0f})")
    return EXIT_OK


def cmd_eval(args: argparse.Namespace) -> int:
    """Altın seti çalıştır ve beklentilerle karşılaştır."""
    result = run_golden(args.golden)
    if args.as_json:
        print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
    else:
        print(render_golden_text(result))
    return EXIT_OK if result.passed else EXIT_FAILED


def cmd_kinds(_args: argparse.Namespace) -> int:
    """Madde türlerini ve her türün kalıplarını yazdır."""
    print(f"clause-cite {__version__} · madde türleri ve örnek kalıplar")
    for kind, patterns in kinds_overview():
        print("")
        print(f"  {kind.label_tr} ({kind.value}) — {len(patterns)} kalıp")
        for pattern in patterns:
            print(
                f"      [{pattern.signal}] {pattern.label_tr} · kip: {pattern.modality.label_tr} · dil: {pattern.lang}"
            )
    print("")
    print(f"  toplam kalıp: {len(PATTERNS)}")
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    """Giriş noktası; hataları belgelenmiş çıkış kodlarına eşler."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return EXIT_INPUT_ERROR
    handlers = {"extract": cmd_extract, "verify": cmd_verify, "eval": cmd_eval, "kinds": cmd_kinds}
    try:
        return handlers[args.command](args)
    except FileNotFoundError as exc:
        print(f"dosya bulunamadı: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR
    except ValueError as exc:
        print(f"girdi hatası: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR
