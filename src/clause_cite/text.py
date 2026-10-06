"""Belge yükleme ve cümle bölme.

İki kural:

* **Yükleme** yalnızca ``.txt`` ve ``.md`` kabul eder; eksik dosya ve boş belge anlamlı Türkçe
  hatayla reddedilir (CLI bunları çıkış kodu 2'ye çevirir).
* **Cümle bölme** satır sonunu ve cümle sonu noktalamasını sınır sayar; Türkçe/İngilizce
  kısaltmalar (``vb.``, ``bkz.``, ``Md.``, ``No.``, ``Sn.``, ``Dr.``, ``etc.``) ve sayı içindeki
  noktalar (``1.234,56``, ``15.03.2026``) cümle sonu **sayılmaz**. Her cümle gerçek satır aralığını
  taşır ve ``text`` alanı kaynak satırın birebir parçasıdır (bu yüzden alıntı doğrulanabilir).
"""

from __future__ import annotations

import re
from pathlib import Path

from clause_cite.models import Document, Sentence

SUPPORTED_SUFFIXES: frozenset[str] = frozenset({".txt", ".md"})

_ABBREVIATIONS: tuple[str, ...] = (
    "vb.",
    "vs.",
    "bkz.",
    "md.",
    "no.",
    "sn.",
    "dr.",
    "av.",
    "doç.",
    "prof.",
    "sf.",
    "ör.",
    "yy.",
    "etc.",
    "e.g.",
    "i.e.",
    "inc.",
    "ltd.",
    "co.",
    "fig.",
    "art.",
)
_INITIAL = re.compile(r"(?:^|[\s(\"'])[A-ZÇĞİÖŞÜ]\.[\"']?$")
_TRAILING_TOKEN = re.compile(r"(\S+)$")


def load_document(path: Path) -> Document:
    """Bir ``.txt``/``.md`` belgesini satırlara ayırarak yükle.

    Raises:
        FileNotFoundError: Dosya yoksa.
        ValueError: Dosya değilse, uzantı desteklenmiyorsa, UTF-8 çözülemiyorsa ya da belge boşsa.
    """
    if not path.exists():
        msg = f"belge bulunamadı: {path}"
        raise FileNotFoundError(msg)
    if not path.is_file():
        msg = f"belge bir dosya değil: {path}"
        raise ValueError(msg)
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        msg = f"desteklenmeyen uzantı: '{path.suffix}' (yalnızca .txt ve .md kabul edilir)"
        raise ValueError(msg)
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        msg = f"belge UTF-8 olarak okunamadı: {path} ({exc})"
        raise ValueError(msg) from exc
    raw = raw.lstrip("\ufeff")
    lines = tuple(raw.splitlines())
    if not any(line.strip() for line in lines):
        msg = f"belge boş: {path}"
        raise ValueError(msg)
    return Document(name=path.name, path=str(path), lines=lines)


def _next_nonspace(line: str, start: int) -> str:
    """``start`` konumundan itibaren boşluk olmayan ilk karakteri (yoksa ``''``) döndür."""
    index = start
    while index < len(line) and line[index] == " ":
        index += 1
    return line[index] if index < len(line) else ""


def _is_abbreviation(prefix: str) -> bool:
    """Nokta dahil önek bir kısaltmayla bitiyorsa ``True``."""
    lowered = prefix.lower()
    return any(lowered.endswith(abbreviation) for abbreviation in _ABBREVIATIONS)


def _ends_sentence(line: str, index: int) -> bool:
    """``line[index]`` bir cümle sonu mu? Sayı ve kısaltma istisnalarını uygular."""
    char = line[index]
    if char in "!?":
        return True
    # char == "."
    prefix = line[: index + 1]
    before = line[:index]
    previous = line[index - 1] if index > 0 else ""
    following = _next_nonspace(line, index + 1)
    if previous.isdigit() and following.isdigit():
        return False  # ondalık ya da tarih: 1.234,56 / 15.03.2026
    token_match = _TRAILING_TOKEN.search(before)
    token = token_match.group(1) if token_match else ""
    if token.isdigit():
        return False  # madde/sıra numarası: "1." veya "Md. 5."
    if _is_abbreviation(prefix):
        return False  # vb. / bkz. / Md. / Dr. ...
    return not _INITIAL.search(prefix)


def _flush(sentences: list[Sentence], buffer: list[str], start_line: int, end_line: int) -> None:
    """Toplanan karakterleri bir cümleye çevir (boşsa atla)."""
    text = "".join(buffer).strip()
    if text:
        sentences.append(Sentence(text=text, start_line=start_line, end_line=end_line))


def split_sentences(document: Document) -> list[Sentence]:
    """Belgeyi cümlelere ayır; her cümle gerçek satır aralığını ve birebir metni taşır."""
    sentences: list[Sentence] = []
    buffer: list[str] = []
    start_line = 0
    end_line = 0
    for line_number, line in enumerate(document.lines, start=1):
        for index, char in enumerate(line):
            if not buffer:
                if char.isspace():
                    continue
                start_line = line_number
            buffer.append(char)
            end_line = line_number
            if char in ".!?" and _ends_sentence(line, index):
                _flush(sentences, buffer, start_line, end_line)
                buffer = []
        # Satır sonu da bir sınırdır: cümleler satırlar arasında birleşmez.
        _flush(sentences, buffer, start_line, end_line)
        buffer = []
    return sentences
