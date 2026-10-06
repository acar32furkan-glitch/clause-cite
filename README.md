# clause-cite

Deterministik sözleşme ve şartname madde çıkarma aracı. Metinlerden yükümlülük, yasak, termin, tutar ve belge zorunluluğu gibi maddeleri çıkarır; her maddeye orijinal alıntı ve `dosya:satır` referansı ekler.

## Neden var?

Hukuki metinler dağınık ve yüksek risklidir. Özellikle "30 gün içinde", "must", "shall not" ve benzeri ifadeleri doğru şekilde ayırmak kritik öneme sahiptir. `clause-cite`, bu ayrımı güvenli, tekrarlanabilir ve kanıtlanabilir şekilde yapar.

## Özellikler

- Her madde için tek alıntı ve kaynak referansı
- `must` / `should` / `may` ayrımı korunur
- Yetersiz veya belirsiz bilgiler `needs_review` ile işaretlenir
- `--anchor` ile göreli tarih ve süreler çözümlenir
- CI ve PR güvenlik kontrolü için hazır
- JSON, CSV ve Markdown çıktıları desteklenir

## Hızlı kullanım

```bash
git clone https://github.com/acar32furkan-glitch/clause-cite && cd clause-cite
uv sync --all-extras --dev
uv run clause-cite extract examples/data/*.txt --anchor 2026-01-01
```

## Temel komutlar

```bash
uv run clause-cite extract examples/data/*.txt --anchor 2026-01-01
uv run clause-cite verify examples/data/*.txt
uv run clause-cite eval examples/golden
uv run clause-cite --version
```

## Çıkış kodları

- `0`: temiz / politikaya uygun
- `1`: çözülmemiş veya belirsiz madde / alıntı ihlali
- `2`: girdi hatası

## Lisans

MIT
