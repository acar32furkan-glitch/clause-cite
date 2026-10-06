# Katkı Rehberi

Teşekkürler! Bu proje **kanıtlı ve deterministik kalmayı** bir tasarım ilkesi olarak benimser;
katkıların tamamı bu çizgide olmalıdır.

## Hızlı kurulum

```bash
git clone https://github.com/acar32furkan-glitch/clause-cite
cd clause-cite
uv sync --all-extras --dev
uv run clause-cite extract examples/data/*.txt --anchor 2026-01-01   # kimlik bilgisi gerekmez
uv run clause-cite verify examples/data/*.txt
uv run pytest
```

## Değişmez kurallar (pazarlık dışı)

1. **Alıntısız madde yok.** Her `Item` birebir alıntı + `(dosya, satır_başı, satır_sonu)` taşımak
   zorundadır. Bir kalıp alıntı üretemiyorsa **madde çıkarmaz**; `verify` bu invariyantı bağımsız
   olarak kanıtlar (bkz. `docs/adr/0001-citation-invariant.md`).
2. **Modality birleştirilmez.** `must`/`should`/`may` ayrı kalır; çatışma varsa öncelik
   `yasak > zorunluluk > izin` uygulanır **ve** madde `needs_review` işaretlenir
   (bkz. `docs/adr/0002-modality-preserved.md`).
3. **Ağ çağrısı yok, saat okuma yok, rastgelelik yok.** Çıkarım saf fonksiyondur; zaman `anchor`
   ile dışarıdan verilir. Bir kalıp ağa çıkıyorsa tasarım tartışması gerekir.
4. **Uydurma yok.** Aktör veya tarih metinden çıkarılamıyorsa `unresolved` kalır. Boşluğu tahminle
   doldurma dürtüsü doğduğunda cevap `needs_review`'dir, en yakın tahmin değil.
5. **Türkçe metin, İngilizce alan adı.** Madde mesajları ve dokümanlar Türkçe; kod/alan/kod adları
   (`ItemKind`, `extract`, `--anchor`) İngilizce.

## Yeni kalıp ekleme adımları

1. `src/clause_cite/` içindeki kalıp modülüne saf bir sinyal ekle: girdi bölütlenmiş cümle, çıktı
   eşleşme (`kind`, `modality`, `matched_span`) olsun. Kalıbı `docs/rules.md` tablosuna yaz.
2. **Tür ve modality'yi ayrı ayrı belirle.** Bir kalıp türü söylerken modality'yi varsayılan bırakma;
   hangi sinyalden türediğini açıkça yaz (`must` / `should` / `may`).
3. **Alıntıyı ve satır aralığını koru.** Kalıp, eşleştiği cümlenin birebir metnini ve satır aralığını
   taşımalı; kısaltma, normalizasyon veya "düzeltilmiş" alıntı yok.
4. **Çakışmayı gizleme.** İki kalıp aynı cümleye düşerse önceliği uygula **ve** `needs_review` bayrağı
   bırak; sessizce birini seçme.
5. Test yaz: sınır durumları, kalıbın susması gereken durumlar (eksik veri → madde yok), modality
   çatışması ve determinizm (aynı girdi iki kez → aynı çıktı).
6. Altın seti güncelle: yeni davranış `examples/golden` vakalarına yansımalı; beklenti değiştiyse
   commit mesajında gerekçesini yaz ve `uv run clause-cite eval examples/golden` ile doğrula.
7. Dokümantasyonu güncelle: `docs/rules.md` (kalıp kataloğu) ve gerekirse `docs/architecture.md` ve
   `docs/roadmap.md`.

## Yanlış pozitif bildirimi ve kapsam zorunluluğu

- Bir **yanlış madde** veya kaçırılan madde bildirirken lütfen **kaynak cümleyi** paylaşın (mümkünse
  kısaltarak): kalıp, metne bakan bir fonksiyondur ve örnek olmadan düzeltilemez.
- Her yeni kalıp, o kalıbın **neyi kapsamadığını** da yazmalıdır. "Şunu da yakalar" cümlesi kadar
  "şunu yakalamaz" cümlesi de zorunludur — sessiz sınır, en tehlikeli sınırdır.

## Kalite kapıları

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy                              # strict
uv run pytest --cov=clause_cite --cov-report=term-missing --cov-fail-under=85
uv run clause-cite verify examples/data/*.txt   # alıntı invariyantı
uv run clause-cite eval examples/golden         # altın set
```

## Commit ve PR

- Conventional Commits: `feat(patterns): ...`, `fix(verify): ...`, `docs: ...`, `test: ...`.
- PR açıklamasında: ne değişti, neden, hangi kalıp/tür etkilendi, alıntı invariyantı ve modality
  korunumu hâlâ sağlanıyor mu.
- Yeni bir kalıp eklediyseniz `examples/data/` altına örnek bir metin parçası koyun.
