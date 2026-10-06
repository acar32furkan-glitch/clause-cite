## Ne değişti?

<!-- Kısa özet. Örnek: "'en geç ... içinde' artık TERMİN + ZORUNLU olarak çıkarılıyor" -->

## Neden?

<!-- Hangi metin sınıfı yakalanıyor: Closes #12 -->

## Etkilenen kalıp / tür

- [ ] Yeni veya değişen sinyal kalıbını yazdım (`docs/rules.md` tablosunu güncelledim)
- [ ] Yeni bir madde türü eklendiyse `ItemKind` ve Türkçe karşılığı eklendi, `clause-cite kinds` güncellendi
- [ ] `uv run clause-cite extract examples/data/*.txt --anchor 2026-01-01 --json` yerelde çalışıyor

## Kanıt ve determinizm kontrol listesi

- [ ] Her yeni madde birebir alıntı + `dosya:satır` taşıyor (alıntı invariyantı)
- [ ] `uv run clause-cite verify examples/data/*.txt` temiz geçiyor
- [ ] Modality (`must`/`should`/`may`) birleştirilmiyor; belirsizlik görünür kalıyor
- [ ] Aktör/tarih bilinmiyorsa `unresolved` kalıyor (uydurulmuyor)
- [ ] Zaman çapadan (`--anchor`) geliyor, `datetime.now()` çağrılmıyor
- [ ] Altın set (`examples/golden`) beklentileri güncellendi ve `clause-cite eval examples/golden` geçiyor

## Kontrol listesi

- [ ] `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest` geçiyor
- [ ] Dokümantasyon güncellendi (`docs/rules.md`, gerekirse `docs/architecture.md` ve `docs/roadmap.md`)
