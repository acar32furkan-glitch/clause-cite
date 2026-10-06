# ADR-0002 — Modality korunur: must / should / may asla birleştirilmez

- **Durum:** Kabul edildi
- **Tarih:** 2026-10-06

## Bağlam: "birleştirme" cazibesi

Bir çıkarım aracı, maddeleri "yapılacaklar listesi"ne indirgemek ister. Listenin akıcı olması için
anlaşılır bir dürtü doğar: `must`, `should` ve `may` fiillerini tek bir "aksiyon" kavramında birleştir
— sonuçta hepsi "yapılacak bir şey"dir. Bu dürtü üç şeyi yok eder:

- **Hukuki ağırlık farkı.** "Taraflar toplantı tutanağını saklamalıdır" ile "Taraflar tutanağı
  saklamak zorundadır" aynı şey değildir. Zorunluluk ihlal edilirse yaptırım doğabilir; öneri ihlal
  edilirse doğmaz.
- **Belirsizliğin görünürlüğü.** Zayıf bir sinyal (`may`, `should`) güçlü bir sinyalin (`must`)
  yanında erirse, kullanıcı aslında belirsiz olan bir maddeyi kesin sanır.
- **Denetlenebilirlik.** Birleştirme geri alınamaz: kullanıcı orijinal modality'yi kaynaktan tekrar
  çıkarmak zorunda kalır — ki zaten araç bunu yapıyor.

## Karar

**Modality üç değerden biri olarak aynen taşınır ve asla birleştirilmez.**

| Sinyal | Türkçe | Anlam |
|--------|--------|-------|
| `must` | ZORUNLU | İhlali yaptırım doğurabilen yükümlülük ("zorundadır", "shall", "must") |
| `should` | ÖNERİLEN | Tavsiye; ihlali yükümlülük doğurmaz ("malıdır", "tavsiye edilir", "should") |
| `may` | OPSİYONEL | İzin/yetki; yapmak da yapmamak da serbesttir ("abilir", "yetkilidir", "may") |

- **Türkçe nüans korunur.** "-melidir" (öneri) ile "-mek zorundadır" (zorunluluk) ayrı modality'dir;
  ikisi de aynı "aksiyon" havuzuna düşmez (bkz. [kalıp kataloğu](../rules.md)).
- **Çakışmada öncelik: yasak > zorunluluk > izin.** Bir cümlede birden fazla sinyal varsa **en güçlü**
  sinyal seçilir (seçim, birleştirme değil) **ve** madde `needs_review` ile işaretlenir. Çatışma
  gizlenmez, görünür kalır.
- **Tanımda modality yoktur.** Bir tanım cümlesi hüküm değildir; `modality: null` taşır ve
  zorunluluk/öneri arasından bir değer **atamaz**.
- **Belirsizlik erimez.** Kalıp modality kararını veremiyorsa madde `ambiguous` olur; yine de madde
  sessizce düşmez, `needs_review` ile çıkar.

## Sonuçlar

- **Kazanç — hukuki doğruluk.** Rapor, "ne yapmalıyım?" sorusunu değil, "metinde hangi yükümlülük
  hangi ağırlıkta?" sorusunu doğru cevaplar. Bir hukukçu çıktıdan doğrudan ağırlık okuyabilir.
- **Kazanç — görünür belirsizlik.** Çatışan sinyal bir hata değil bir **bayraktır**; insanın bakması
  gereken yeri işaretler. Kullanıcı belirsizliği araçtan değil, kendi kararından yönetir.
- **Kazanç — kayıpsız filtreleme.** Modality korunduğu için kullanıcı çıktıyı modality'ye göre
  güvenle filtreleyebilir ("yalnızca ZORUNLU maddeleri göster"); birleştirilmiş çıktıda bu imkânsız
  olurdu.
- **Bedel — daha az çıkarma.** Bazı cümleler modality belirsiz olduğu için `ambiguous` + `needs_review`
  olarak işaretlenir ve kullanıcı bunları elle eler. Bu, akıcı bir liste değil **doğru** bir liste
  üretir; tercih bilinçlidir.
- **Kural.** Modality'yi birleştirme veya "en yükseğe yükseltme" dürtüsü doğduğunda cevap **hayır**dır:
  belirsizlik bir kusur değil, çıktının parçasıdır. Bu kural [ADR-0001](0001-citation-invariant.md)
  ile birlikte, çıktıyı "doğrulanabilir ve doğru ağırlıkta" tutar.
- **Kapsam dışı.** Modality'nin hukuki yorumu (örnek: "shall" belirli bir yargı çevresinde ne
  doğurur?) bu aracın işi değildir; araç sinyali korur, yorumu hukukçu yapar.
