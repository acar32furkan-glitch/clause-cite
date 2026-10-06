# Kalıp Kataloğu

clause-cite bir metni **cümle cümle** tarar ve her cümleyi kalıplarla eşler. Her kalıp iki şeyi
söyler: **tür** (`ItemKind`) ve **kip** (`Modality`). Çıkarımın tek bir değişmez koşulu vardır:

> **Alıntısı gösterilemeyen cümle maddeye dönüşmez.** Kalıp, eşleştiği cümlenin birebir metnini ve
> `dosya:satır` aralığını taşıyamıyorsa madde çıkarılmaz (bkz.
> [ADR-0001](adr/0001-citation-invariant.md)).

Kalıplar **veridir, kod değildir**: sinyal sözlükleri (`tr`/`en`/`neutral`) `patterns.py` içinde veri
olarak tutulur, yeni bir kalıp eklemek çıkarım mantığını değiştirmez. `--lang auto` belgeyi tarayan
tüm kalıpları uygular; `tr`/`en` ilgili dili **ve** `neutral` kalıpları (ör. para biçimi) uygular.

## Öncelik kuralı — yasak > zorunluluk > izin

Aynı cümlede birden fazla kalıp eşleşirse **iki bağımsız öncelik** uygulanır.

**Kip önceliği** (`MODALITY_PRIORITY`): `must` > `should` > `may` — yani zorunluluk > izin.

**Tür önceliği** (`KIND_PRIORITY`):

| Güç | Tür | Örnek |
|-----|-----|-------|
| 1 (en güçlü) | `prohibition` · YASAK | "... yapamaz", "shall not", "must not" |
| 2 | `document_required` · BELGE_ZORUNLU | "sunulması zorunludur", "shall submit" |
| 3 | `obligation` · YÜKÜMLÜLÜK | "... zorundadır", "-melidir", "shall", "must" |
| 4 | `deadline` · TERMİN | "30 gün içinde", "within 30 days" |
| 5 | `money` · PARA | "1.234,56 TL", "penalty of" |
| 6 | `definition` · TANIM | "ifade eder", "means" |
| 7 (en zayıf) | `ambiguous` · BELİRSİZ | "makul süre", "as applicable" |

Güçlü bir tür, zayıf bir türü yutar; ama **kip sinyalleri korunur**: eşleşen **tüm** kalıplar
`Item.signals` alanına yazılır. Çatışma sessizce "en güçlü kazandı" diye kapatılmaz; madde
`needs_review` ile işaretlenir — çünkü çakışma çoğu zaman gerçek bir çelişki değil, eksik bir
kalıbdır ve insanın bakması gerekir.

## 1. Yükümlülük (`obligation` → YÜKÜMLÜLÜK)

| Yön | Sinyal | Kip | Örnek cümle |
|-----|--------|-----|-------------|
| TR | `-mak/-mek zorundadır`, `zorundadır`, `yükümlüdür`, `gerekir/gereklidir` | `must` | "Yüklenici, hizmeti ... ifa etmek **zorundadır**." |
| TR | `-melidir / -malıdır` (kesin yükümlülük) | `must` | "Yüklenici, sigorta primlerini **ödemelidir**." |
| TR | `-meli / -malı` (öneri tonlu), `önerilir / tavsiye edilir` | `should` | "Taraflar tutanağı **saklamalıdır**." |
| TR | `-abilir/-ebilir`, `hakkı vardır` (izin) | `may` | "İdare, hizmeti **denetleyebilir**." |
| EN | `shall`, `must`, `is required to` | `must` | "The Supplier **shall** deliver within 30 days." |
| EN | `should` | `should` | "The parties **should** retain the minutes." |
| EN | `may`, `is entitled to` | `may` | "The Buyer **may** reject non-conforming goods." |

- **Türkçe nüans korunur:** `-melidir/-malıdır` kesin yükümlülük (`must`), çıplak `-meli/-malı` ise
  öneri tonlu (`should`) sayılır (bkz. [ADR-0002](adr/0002-modality-preserved.md)).
- İzin kalıpları (`-abilir`, `hakkı vardır`, `may`) ayrı bir "izin" türü **değildir**: tür
  `obligation`, kip `may` olur. Ayrım türde değil **kipte** yaşar.

## 2. Yasak (`prohibition` → YASAK)

| Yön | Sinyal | Kip | Örnek cümle |
|-----|--------|-----|-------------|
| TR | `yasaktır`, `-mamalıdır/-memelidir`, `-maz/-mez`, `edemez`, `izin verilmez` | `must` | "Personelin ... alkol kullanması **yasaktır**." |
| EN | `shall not`, `must not`, `may not`, `prohibited`, `not permitted` | `must` | "This Agreement **shall not** be assigned." |

- **Neden `must`?** Bir yasağın derecesi yoktur: yapılmaması **zorunlu** olan eylemdir. `prohibition`
  bir *tür*dür; kipi her zaman `must`'tur (izin → yasak ekseninde "izin verilmez").

## 3. Termin (`deadline` → TERMİN)

| Yön | Sinyal | Kip | Örnek cümle |
|-----|--------|-----|-------------|
| TR | `en geç`, `tarihine kadar`, `tarihten itibaren`, `N gün/ay ... içinde` | varsayılan `may` | "Ödeme, fatura tarihinden itibaren **30 gün içinde** yapılır." |
| EN | `within N days`, `no later than`, `by <tarih>` | varsayılan `may` | "Payment is due **within** 15 days." |

- Termin kalıbı **süreyi** bulur: kesin bir tarih (`2026-03-15`) ya da göreli bir süre (`30 gün`).
- **Varsayılan kip `may`'dir.** Cümlede ayrıca bir yükümlülük kalıbı varsa tür önceliği yükümlülüğe
  kayar ve süre o maddenin termini (`due_date`/`due_raw`) olarak taşınır; kip yükümlülükten gelir.
- **Göreli süre ancak bir çapayla kesinleşir.** `--anchor 2026-01-01` verilirse `30 gün` →
  `2026-01-31` olur ve güven yükselir. Çapa yoksa tarih `unresolved` kalır, ham metin (`due_raw`)
  korunur ve madde `needs_review` alır. **Tahmini tarih üretilmez.**

## 4. Para (`money` → PARA)

| Yön | Sinyal | Kip | Örnek cümle |
|-----|--------|-----|-------------|
| TR | `1.234,56 TL`, `₺`, `lira` | varsayılan `may` | "Gecikme halinde **1.234,56 TL** ceza uygulanır." |
| EN | `USD`, `EUR`, `$`, `€` | varsayılan `may` | "A **penalty of USD 5,000** applies." |

- Tutarlar `Decimal` üzerinden işlenir; float'a düşülmez ve iki ondalığa `ROUND_HALF_UP` ile yuvarlanır.
  TR (`1.234,56`) ve EN (`5,000.00`) binlik/ondalık ayırıcı ayrımı para birimine göre yapılır.
- Para birimi kaynakta geçtiği hâliyle korunur (`TL`, `TRY`, `USD`, `₺`, `$`, `€`). Bir para birimi
  belirteci **zorunludur**; çıplak bir sayı (`30`) tutar sayılmaz.

## 5. Belge zorunlu (`document_required` → BELGE_ZORUNLU)

| Yön | Sinyal | Kip | Örnek cümle |
|-----|--------|-----|-------------|
| TR | `sunulması zorunludur`, `teslim edilmesi gerekir`, `ibraz edilmesi gerekir`, `sağlanması zorunludur`, `sunulmalıdır` | `must` | "Fatura ve irsaliyenin ... **sunulması zorunludur**." |
| EN | `shall provide/submit/deliver`, `must be submitted`, `shall be provided` | `must` | "The Seller **must submit** the certificate of origin." |

- Belge zorunluluğu "hangi belge, ne zaman" sorusunu ikiye ayırır: belge adı bu kalıptan, zaman ise
  ayrı bir `deadline` kalıbından gelir. İkisi aynı cümledeyse tür önceliği belgeye kayar.

## 6. Tanım (`definition` → TANIM)

| Yön | Sinyal | Kip | Örnek cümle |
|-----|--------|-----|-------------|
| TR | `ifade eder`, `olarak tanımlanır`, `anlamına gelir`, `olarak anlaşılır` | `may` (nötr) | "'Hizmet', ... temizlik faaliyetlerini **ifade eder**." |
| EN | `means`, `is defined as`, `refers to` | `may` (nötr) | "'Confidential Information' **means** any disclosed data." |

- Tanım cümlesi bir **hüküm değildir**: hiçbir tarafa yükümlülük yüklemez. Motor tanım kalıplarını
  `may` kipiyle işaretler (nötr varsayılan) — bunu `must` sanan bir çıkarım yanlış alarm olurdu.

## 7. Belirsiz (`ambiguous` → BELİRSİZ)

| Yön | Sinyal | Kip | Örnek cümle |
|-----|--------|-----|-------------|
| TR | `ayrıca belirlenir`, `taraflarca kararlaştırılır`, `makul süre`, `uygun görülen`, `ihtiyaç halinde` | `may` | "Uygun görülen tedbirler alınır." |
| EN | `as determined`, `to be agreed`, `reasonable time`, `as applicable`, `from time to time` | `may` | "Delivery shall occur **as applicable**." |

Kalıp eşleşti ama tür kararı verilemediğinde madde `ambiguous` olur: hiçbir zaman sessizce
düşürülmez, güven düşük kalır ve **daima** `needs_review` ile çıkar. Bu bir karar değil, bir
**soru**dur; insana verilir.

## Güven skoru ve `needs_review`

Güven, bağımsız sinyal sayısı ile netleşen aktör/tarih/tutar durumundan hesaplanır:

| Güven (kod / etiket) | Koşul |
|----------------------|-------|
| `high` · YÜKSEK | Birden çok sinyal ya da net aktör **ve** tarih/tutar; çözülemeyen alan yok |
| `medium` · ORTA | Kalıp net ama aktör **veya** tarih/tutar eksik |
| `low` · DÜŞÜK | Zayıf sinyal; çözülemeyen göreli tarih, çözülemeyen taraf ya da tek başına güçsüz kalıp |

Puan: her kalıp sinyali +1; çözülmüş aktör +1; çözülmüş tarih **veya** tutar +1; çözülemeyen göreli
tarih −1; çözülemeyen taraf −1. Toplam ≥3 → `high`, ≥2 → `medium`, aksi `low`.

Bir madde şu durumların **herhangi birinde** `needs_review` bayrağı alır:

| Tetikleyici | Neden |
|-------------|-------|
| Taraf çözülemedi (`actor_resolved == False`) | "Kim yapmalı?" metinden çıkmıyor |
| Taraf metinde hiç geçmiyor (`actor is None`, `actor_resolved == True`) | Edilgen cümle: sahip atanmalı. Konsolda "aktör: (metinde belirtilmemiş)" yazar — "çözülemedi" ile karıştırılmaz |
| Tür `definition` | İnsan çıktısında kip etiketi gösterilmez (`—`): "X, ... ifade eder" opsiyonel ya da zorunlu değildir. Kip bilgisi JSON/CSV'de korunur |
| Göreli termin var, `--anchor` yok (`due_raw` dolu, `due_date` boş) | Tarih `unresolved` kalır; uydurulmaz |
| Güven `low` | Karar zayıf; sessiz kalmak yanlış olur |

`needs_review` maddeyi **gizlemez**; yalnızca işaretler. `--fail-on-unresolved` bu bayrağı CI'da
kırmızıya çevirmenin yoludur.

## Neden bu kalıplar?

- **Kapsam dar tutuldu.** Her kalıp metinde **açık** bir sinyal arar (`shall not`, `zorundadır`,
  `within`). Dolaylı çıkarım yapılmaz: açık bir süre ifadesi yoksa cümle termin sayılmaz. Yanlış bir
  madde, kaçırılan bir maddeden daha pahalıdır çünkü insanı yanlış yere yönlendirir.
- **Türkçe ve İngilizce ayrı yazıldı.** `-melidir` ile `-meli` aynı şey değildir; `shall` ile
  `should` aynı şey değildir. İki dili tek bir kip havuzunda eritmek ADR-0002'yi ihlal ederdi.
- **Kalıp veri, motor sabittir.** Yeni bir sinyal eklemek çıkarım motorunu değiştirmez; yalnızca
  `PATTERNS` demetine bir satır ekler. Bu, kalıpların test edilebilir ve denetlenebilir kalmasını
  sağlar.
- **Şüphe bir çıktıdır.** `ambiguous` ve `needs_review`, sistemin "bilmiyorum" deme biçimidir. Bir
  hukuk/uyum aracında "bilmiyorum"u gizlemek, bilmediğini söylemekten çok daha tehlikelidir.

## Kapsam dışı

- **Cümleler arası çıkarım.** İki maddeyi birleştirip yeni bir hüküm üretilmez (çoklu belge/çelişki
  analizi yol haritasındadır, bkz. [roadmap.md](roadmap.md)).
- **Hukuki yorum.** Kalıp "bu bir yükümlülüktür" der; "bu yükümlülük şu anlama gelir" demez.
- **PDF/DOCX/tablo.** v0.1 girdisi düz metindir (`.txt`/`.md`); PDF ve tablo çıkarımı v0.2'dedir.
- **Örtük/örtülü ifadeler.** Açık sinyali olmayan eş anlamlılar (ör. "makul sürede" dışındaki
  yorum gerektiren ifadeler) yakalanmaz; emin olunamayan her şey ya susar ya `needs_review` olur.
