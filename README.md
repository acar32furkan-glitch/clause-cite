# clause-cite

[![CI](https://github.com/acar32furkan-glitch/clause-cite/actions/workflows/ci.yml/badge.svg)](https://github.com/acar32furkan-glitch/clause-cite/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Ruff](https://img.shields.io/badge/lint-ruff-261230)](https://docs.astral.sh/ruff/)
[![Checked with mypy](https://img.shields.io/badge/mypy-strict-2f6f9f)](https://mypy-lang.org/)

**Türkçe** · [English](README.en.md)

**Sözleşme, yönetmelik ve şartname metinlerini kanıtlı aksiyon maddelerine çeviren deterministik
CLI.** Her madde **birebir alıntı + `dosya:satır` aralığı** taşır; alıntısı gösterilemeyen bir şey
çıkarılmaz. Ağ yok, LLM yok, saat dışarıdan gelir.

> ⚖️ **Bu araç hukuki tavsiye DEĞİLDİR.** clause-cite yalnızca bir metinden yapılandırılmış maddeler
> (yükümlülük, yasak, termin, tutar, belge zorunluluğu, tanım) çıkarır ve her birini kaynağına
> bağlar. Belgeyi yorumlamaz, hukuki sonuç doğurmaz ve hukuki görüş yerine geçmez. Nihai değerlendirme
> yetkin bir hukukçuya aittir (bkz. [SECURITY.md](SECURITY.md)).

Kimlik bilgisi yok, ağ yok, 30 saniyede görün:

```bash
git clone https://github.com/acar32furkan-glitch/clause-cite && cd clause-cite
uv sync --all-extras --dev
uv run clause-cite extract examples/data/*.txt --anchor 2026-01-01
```

> `--anchor` **gereklidir** ve saati dışarıdan verir: göreli bir termin ("30 gün içinde") ancak bir
> çapa tarihine göre kesinleşir. Çapa verilmezse göreli süreler `unresolved` kalır — uydurulmaz.
> Ağı ve saati okumadığımız için aynı girdi + aynı çapa her zaman aynı çıktıyı üretir.

![clause-cite çıktısı](docs/assets/demo.svg)

---

## Neden?

Sözleşmeler, yönetmelikler ve şartnameler yükümlülükle dolu ama insan gözü için dağınıktır: "teslimat
30 gün içinde" bir maddede, "gecikme halinde günlük %0,5 ceza" başka bir maddede, "poliçe ekte
sunulacaktır" bir üçüncüsünde. Bunları elle çıkarmak yavaş ve hataya açıktır; bir özet aracına
özetletmek ise tehlikelidir — çünkü **özet, alıntılanamayan cümleler üretir.**

clause-cite bunu deterministik biçimde çözer:

- **Alıntısız madde yok.** Her madde, kaynaktaki **birebir metni** ve `dosya:satır` aralığını taşır;
  `verify` komutu bu invariyantı kanıtlar. Gösterilemeyen bir şey çıkarılmaz
  (bkz. [ADR-0001](docs/adr/0001-citation-invariant.md)).
- **Modality korunur.** `must` / `should` / `may` **asla birleştirilmez**; belirsizlik görünür kalır.
  "Yapmalı" ile "yapmak zorunda" arasındaki fark hukuki sonuç doğurur
  (bkz. [ADR-0002](docs/adr/0002-modality-preserved.md)).
- **Uydurma yok.** Aktör veya tarih metinden çıkarılamıyorsa `unresolved` kalır; sistem boşluğu
  tahminle doldurmaz. Emin olmadığında madde `needs_review` bayrağı alır.

## Türler (`ItemKind`)

| Tür (kod) | Türkçe karşılık | Ne yakalar |
|-----------|-----------------|------------|
| `obligation` | **YÜKÜMLÜLÜK** | Bir tarafa yapması gereken bir şey yükler ("...mak zorundadır", "-melidir", "shall", "must") |
| `prohibition` | **YASAK** | Bir eylemi yasaklar ("...amaz", "shall not", "must not") |
| `deadline` | **TERMİN** | Bir tarih veya süre sınırı ("30 gün içinde", "en geç ...", "within", "no later than") |
| `money` | **PARA** | Tutar, ceza, ödeme ("10.000 TL", "%0,5 gecikme cezası", "penalty of") |
| `document_required` | **BELGE_ZORUNLU** | Belge/evrak sunma zorunluluğu ("sunulması zorunludur", "shall submit", "must be submitted") |
| `definition` | **TANIM** | Bir terimin tanımı ("... olarak ifade edilir", "means", "refers to") |
| `ambiguous` | **BELİRSİZ** | Kalıp eşleşti ama tür/modality kararı verilemedi — daima `needs_review` |

Tür karşılıkları ve sinyal kalıpları: **[docs/rules.md](docs/rules.md)**

## Modality

| Sinyal | Türkçe karşılık | Örnek yüzey biçimleri |
|--------|-----------------|-----------------------|
| `must` | **ZORUNLU** | "...mak/-mek zorundadır", "-melidir / -malıdır", "gerekir", "shall", "must" |
| `should` | **ÖNERİLEN** | "-meli / -malı", "önerilir / tavsiye edilir", "should" |
| `may` | **OPSİYONEL** | "...abilir/-ebilir", "hakkı vardır", "may", "is entitled to" (tanım maddelerinde insan çıktısında kip etiketi gösterilmez) |

Aynı cümlede birden fazla sinyal varsa **en güçlü** olan kazanır; öncelik kuralı
`yasak > zorunluluk > izin`tir ve çakışma maddeye `needs_review` olarak yansır. Modality hiçbir zaman
kaybolmaz veya "birleştirilmiş" bir değere indirgenmez.

## Güven ve `needs_review`

| Güven | Türkçe | Anlam |
|-------|--------|-------|
| `HIGH` | YÜKSEK | Kalıp net; aktör ve tarih/tutar metinden çözüldü |
| `MEDIUM` | ORTA | Kalıp net ama aktör **veya** tarih/tutar çözülemedi |
| `LOW` | DÜŞÜK | Kalıp zayıf, çözülemeyen taraf/tarih var; karar belirsiz |

Bir madde şu durumlarda `needs_review` bayrağı alır: aktör metinden çıkarılamıyorsa; göreli bir termin
var ama `--anchor` yoksa (tarih `unresolved` kalır, ham metin korunur); güven `LOW` ise (tür
`ambiguous` dâhil). `needs_review` **sessiz bir uyarıdır**, maddeyi gizlemez — bayrak, insanın bakması
gereken yeri işaretler.

## Komutlar

```bash
uv run clause-cite extract examples/data/*.txt --anchor 2026-01-01   # maddeleri çıkar
uv run clause-cite verify  examples/data/*.txt                        # alıntı invariyantını kanıtla
uv run clause-cite eval    examples/golden                            # altın set regresyonu
uv run clause-cite kinds                                              # tür ve modality karşılıkları
uv run clause-cite --version
```

`extract` bayrakları:

| Bayrak | Anlam |
|--------|-------|
| `--anchor YYYY-MM-DD` | Göreli süreleri kesinleştiren çapa tarihi (saat dışarıdan) |
| `--json` | Ajan/CI için JSON sözleşmesi |
| `--report out.json` | JSON raporunu dosyaya yaz |
| `--csv out.csv` | Madde tablosunu CSV olarak dışa aktar |
| `--fail-on-unresolved` | `unresolved` veya `needs_review` madde varsa 1 koduyla çık |
| `--strict` | Belirsizlik toleranssız: `ambiguous`/`LOW` madde çıkış kodunu yükseltir |
| `--max-items N` | Çıktıyı ilk N maddeyle sınırla |
| `--github-summary` | Actions iş özetine Markdown raporu ekle |
| `--lang auto\|tr\|en` | Sinyal sözlüğü dili (varsayılan `auto`: belgeden sez) |

## Çıkış kodları

| Kod | Anlam |
|-----|-------|
| `0` | Temiz (çıkarım geçerli, politika karşılandı) |
| `1` | `--fail-on-unresolved` (veya `--strict`) politikası düştü, ya da **alıntı invariyantı ihlali** |
| `2` | Girdi hatası (okunamayan dosya, bozuk kodlama, `--anchor` biçimi geçersiz) |

## CI'da kullanımı

```yaml
- name: Sözleşme maddelerini çıkar
  run: uv run clause-cite extract content/sozlesme.txt --anchor 2026-01-01 --fail-on-unresolved --github-summary
```

`--fail-on-unresolved` çözülemeyen bir madde varsa komutu **1** koduyla çıkarır ve PR'ı kırar;
`--github-summary` iş özetine Markdown raporu ekler. Örnek iş akışı:

```yaml
name: Clause cite
on:
  pull_request:
    paths: ["content/**.txt"]

jobs:
  maddeler:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true
      - run: uv sync --all-extras --dev
      - name: Çıkarım (alıntı zorunlu)
        run: >
          uv run clause-cite extract content/*.txt
          --anchor 2026-01-01 --fail-on-unresolved --github-summary
```

## Mimari

```text
examples/data/*.txt  ─→ text.py ─→ extract.py ─→ Item ─→ verify.py ─→ render/cli
 (belge metni)          (bölütle)   (kalıp)     (alıntı)  (invariyant)   (rapor)
```

- Çıkarım katmanı **saf fonksiyondur**: IO yok, saat yok, rastgelelik yok; zaman `anchor` ile verilir.
- Her `Item` bir `source` taşır: birebir alıntı + `(dosya, satır_başı, satır_sonu)`.
- `verify` bağımsız çalışır: çıktının kaynağa karşı hâlâ doğru olduğunu **kanıtlar**.
- Ayrıntı: [docs/architecture.md](docs/architecture.md) · kararlar: [docs/adr/](docs/adr/)

## Kalite

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy                              # strict
uv run pytest --cov=clause_cite --cov-report=term-missing --cov-fail-under=85
uv run clause-cite verify examples/data/*.txt   # alıntı invariyantı
```

`ruff` + `ruff format` + `mypy --strict` temiz · CI: Python 3.12 ve 3.13 matrisi + "çıkarım demo" işi
(alıntı ve `dosya:satır` biçimi, çıkış kodu ve `verify` doğrulanır). Kurulan yorumlayıcı iş içinde
doğrulanır; yanlış sürümle koşan matris kırmızıya döner.

## Sınırlar

- **Hukuki tavsiye vermez.** Çıkarılan maddeler bir metnin yapılandırılmış hâlidir; hukuki görüş,
  yorum veya sonuç değildir. Bu araç bir hukukçunun yerini almaz.
- **Uydurmaz.** Eksik aktör/tarih `unresolved` kalır; göreli süreler çapasız kesinleşmez.
- **Birleştirmez.** `must`/`should`/`may` ve `YASAK`/`YÜKÜMLÜLÜK` ayrımı korunur.
- **LLM yok.** Anlam çıkarımını kalıplarla yapar; emin olmadığında `needs_review` der ve susar.
- **Belgeyi değiştirmez.** Yalnızca okur ve raporlar; dış bir sisteme yazmaz.

## Katkı

[CONTRIBUTING.md](CONTRIBUTING.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) ·
[SECURITY.md](SECURITY.md) · değişiklikler: [CHANGELOG.md](CHANGELOG.md)

## Lisans

[MIT](LICENSE) © 2026 Furkan Acar (acar32furkan-glitch)
