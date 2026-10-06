# Değişiklik Günlüğü

Bu dosya [Keep a Changelog](https://keepachangelog.com/tr/1.1.0/) biçimini izler ve proje
[Semantic Versioning](https://semver.org/lang/tr/) kullanır.

## [0.1.0] - 2026-10-06

### Eklendi
- **Kanıtlı çıkarım:** sözleşme/yönetmelik/şartname metinlerinden yapılandırılmış aksiyon maddeleri.
  Her madde **birebir alıntı + `dosya:satır` aralığı** taşır; alıntısı gösterilemeyen bir şey
  çıkarılmaz (alıntı invariyantı, bkz. [ADR-0001](docs/adr/0001-citation-invariant.md)).
- **Madde türleri (`ItemKind`):** `obligation`/**YÜKÜMLÜLÜK**, `prohibition`/**YASAK**, `deadline`/
  **TERMİN**, `money`/**PARA**, `document_required`/**BELGE_ZORUNLU**, `definition`/**TANIM**,
  `ambiguous`/**BELİRSİZ**.
- **Modality korunumu:** `must`/**ZORUNLU**, `should`/**ÖNERİLEN**, `may`/**OPSİYONEL** **asla
  birleştirilmez**; çatışan sinyallerde öncelik `yasak > zorunluluk > izin`tir ve çatışma
  `needs_review` olarak görünür kalır (bkz. [ADR-0002](docs/adr/0002-modality-preserved.md)).
- **Güven ve inceleme bayrağı:** `HIGH` / `MEDIUM` / `LOW` güven seviyesi ve `needs_review` bayrağı.
  Göreli termin + `--anchor` yoksa tarih `unresolved` kalır; aktör metinden çıkmıyorsa uydurulmaz.
- **Determinizm:** ağ yok, LLM yok; zaman `--anchor` çapasıyla dışarıdan verilir; aynı girdi + aynı
  çapa her zaman aynı çıktıyı üretir.
- **Komutlar:** `extract`, `verify` (alıntı invariyantını kanıtlar), `eval` (altın set), `kinds`,
  `--version`.
- **`extract` bayrakları:** `--anchor`, `--json`, `--report <dosya>`, `--csv <dosya>`,
  `--fail-on-unresolved`, `--strict`, `--max-items`, `--github-summary`, `--lang {auto,tr,en}`.
- **Çıkış kodları:** `0` temiz, `1` `--fail-on-unresolved`/`--strict` politikası düştü ya da alıntı
  invariyantı ihlal edildi, `2` girdi hatası (okunamayan dosya, bozuk kodlama, geçersiz `--anchor`).
- **Çıktılar:** Türkçe konsol raporu (tür/modality/güven etiketleriyle), `--json` sözleşmesi,
  `--report`/`--csv` dosyaları ve `--github-summary` (Actions iş özeti için Markdown).
- **Kalite:** alıntı invariyantı, modality korunumu ve CLI sözleşmesi testlerle sabitlendi; altın set
  (`examples/golden`) regresyon testleri; `ruff` + `mypy --strict` temiz; kapsam `--cov-fail-under=85`
  ile korunuyor; GitHub Actions CI (Python 3.12 ve 3.13 matrisi) ve Dependabot yapılandırıldı.
- **Dokümantasyon:** mimari, kalıp kataloğu, iki ADR, yol haritası ve gerçek çıktıdan üretilen SVG
  demo (`scripts/make_demo_svg.py` → `docs/assets/demo.svg`).

### Notlar
- **Hukuki tavsiye değildir.** Bu araç bir metni yapılandırır, yorumlamaz (bkz. [SECURITY.md](SECURITY.md)).
