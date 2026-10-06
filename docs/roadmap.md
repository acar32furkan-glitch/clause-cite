# Yol Haritası

Her sürüm tek bir soruya cevap verir. Alıntı invariyantı (ADR-0001) ve modality korunumu (ADR-0002)
her sürümde **korunur**; hiçbir özellik bu iki değişmezi gevşetmez.

## v0.1.0 — Kanıtlı çıkarım (bu sürüm)

- Düz metin (`.txt`) girdisi; cümle bölütleme ve kalıp eşleme.
- Yedi tür: `obligation`, `prohibition`, `deadline`, `money`, `document_required`, `definition`,
  `ambiguous` (Türkçe: YÜKÜMLÜLÜK / YASAK / TERMİN / PARA / BELGE_ZORUNLU / TANIM / BELİRSİZ).
- Modality korunumu (`must`/`should`/`may`) ve öncelik kuralı `yasak > zorunluluk > izin`.
- Güven (`HIGH`/`MEDIUM`/`LOW`) ve `needs_review` bayrağı; göreli terminler için `--anchor` çapası.
- `extract` / `verify` / `eval` / `kinds` komutları; `--json`, `--report`, `--csv`,
  `--fail-on-unresolved`, `--strict`, `--max-items`, `--github-summary`, `--lang`.
- Alıntı invariyantı `verify` ile kanıtlanır; altın set (`examples/golden`) regresyonuyla sabitlenir.

## v0.2.0 — Belge girdisi

Sorunun cevabı: **gerçek belgeler `.txt` değil.**

- **PDF girdisi:** metin katmanı olan PDF'lerden çıkarım (taranmış/görüntü PDF bilinçli olarak
  reddedilir; OCR v0.2 kapsamı dışında, çünkü yanlış OCR yanlış alıntı üretir ve alıntı
  doğrulanamaz).
- **DOCX girdisi:** paragraf tabanlı çıkarım; sayfa/satır aralığı yerine **paragraf indeksi** kaynak
  konumlandırması olarak kullanılır (alıntı yine birebir metindir).
- **Tablo çıkarımı:** tablo hücreleri de madde kaynağı olabilir; alıntı hücre metni + tablo konumu
  olur. Tablo, satır/sütun bağlamı olmadan tek başına yorumlanmaz.
- **Kaynak konum modeli genişler:** `(dosya, satır_başı, satır_sonu)` yanına `(sayfa)` ve
  `(paragraf)` alanları eklenir; `verify` her biçimi ayrı ayrı destekler.

## v0.3.0 — Çoklu belge ve çelişki

Sorunun cevabı: **aynı konu iki belgede farklı yazılmışsa ne olur?**

- **Çoklu belge karşılaştırma:** bir dizi belgeyi birlikte okur, aynı aktör/konu etrafındaki
  maddeleri gruplar.
- **Çelişki raporu:** **aynı konuda iki farklı termin** (örnek: bir belgede "30 gün", diğerinde "45
  gün"), veya aynı konuda çatışan modality (bir belgede "shall", diğerinde "should") tespit edilir ve
  **iki alıntı yan yana** gösterilir.
- Çelişki bir "hüküm" değil bir **soru**dur: rapor otomatik karar vermez, insanı iki kaynağa bağlar.
  Çelişki tespiti de alıntı invariyantına tabidir (iki alıntı da gösterilemezse çelişki bildirilmez).

## v0.4.0 — Opsiyonel LLM hakem (ikincil sinyal)

Sorunun cevabı: **kalıpların kaçırdığı örtük ifadeler görülebilir mi?**

- **LLM yalnızca ikincil sinyaldir.** Bir LLM, çıkarımı **zenginleştirebilir** (örnek: "makul sürede"
  gibi örtük bir ifadeye dikkat çekmek) ama **kapı kararı vermez**: hiçbir madde yalnızca LLM dediği
  için çıkmaz, hiçbir madde yalnızca LLM dediği için düşmez.
- **Alıntı zorunluluğu LLM için de geçerli.** LLM'in önerdiği her madde yine birebir alıntı + konum
  taşımak zorundadır; alıntı kaynakta bulunamazsa öneri **reddedilir** ve `verify` bunu yakalar.
- **Kapalı varsayılan.** LLM opsiyoneldir ve varsayılan kapalıdır; açıldığında ağ çağrısı **yalnızca**
  bu katmanda olur, çekirdek çıkarım çevrimdışı ve deterministik kalır. Sağlayıcı, model ve çıktı
  sürümü saklanır ki rapor yeniden üretilebilsin.

## Kapsam dışı (bilinçli)

- **Hukuki tavsiye vermek.** Araç "bu madde şu anlama gelir / şöyle yapmalısın" demez. Çıkarım,
  yorum değildir; hukuki değerlendirme yetkin bir hukukçuya aittir (bkz. [SECURITY.md](../SECURITY.md)).
- **Belgeyi otomatik imzalamak/göndermek.** Araç belgeyi değiştirmez, imzalamaz, karşı tarafa
  göndermez; yalnızca okur ve raporlar.
- **Dış takip sistemine onaysız yazmak.** Jira/Linear vb. bir sisteme madde açmak bir *teslim*
  kararıdır ve **onay olmadan** yapılmaz; v0.1'de hiç yoktur, ileride bile opt-in olur.
- **Taranmış PDF için OCR.** Yanlış OCR, doğrulanamayan alıntı üretir; bu ADR-0001'e aykırıdır.
- **Belgeyi "özetlemek".** Özet, alıntılanamayan cümleler üretir; clause-cite madde listesi üretir,
  özet değil.
