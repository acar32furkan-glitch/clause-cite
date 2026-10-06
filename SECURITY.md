# Güvenlik Politikası

> ⚖️ **Hukuki tavsiye değildir.** clause-cite bir metinden yapılandırılmış maddeler çıkarır; hukuki
> görüş vermez, belgeyi yorumlamaz ve hukuki sonuç doğurmaz. Çıktı, bir hukukçunun değerlendirmesinin
> yerine geçmez. Bu, bir güvenlik politikasının parçası olacak kadar önemlidir: **çıktıya hukuki
> karar dayanağı olarak güvenmeyin.**

## Desteklenen sürümler

| Sürüm | Destek |
|-------|--------|
| 0.1.x | ✅ |
| < 0.1 | ❌ (geliştirme sürümleri) |

## Bir açığı nasıl bildirirsiniz?

Güvenlikle ilgili konuları herkese açık issue olarak **açmayın**. GitHub üzerinden özel güvenlik
bildirimi gönderin: depoda **Security → Report a vulnerability**. Bildirimde şunları paylaşın:

- etkilenen sürüm ve işletim sistemi,
- en küçük yeniden üretim adımları (girdi belgeleri ve kullanılan `--anchor`),
- beklenen ve gözlenen davranış,
- varsa istismar senaryosu.

İlk yanıt hedefi: 7 iş günü. Düzeltme yayınlandığında bildirimi yapan kişi (isterseniz) sürüm
notlarında anılır.

## Tehdit modeli

`clause-cite` **çevrimdışı bir CLI/kütüphanedir**: belge metnini okur, çıkarım yapar, raporlar. Ağa
çıkmaz, hesap açmaz, kimlik bilgisi istemez ve hiçbir belgeyi **değiştirmez**.

Bu proje açısından anlamlı riskler:

| Risk | Değerlendirme |
|------|---------------|
| Doğruluk riski | Çıkarım hatalıysa **yanlış madde** (olmayan yükümlülük) ya da **kaçırma** (gözden kaçan yükümlülük) olur. İkisi de ciddidir: bir hukuk/uyum ekibi eksik bir maddeyi atlayabilir. Bu yüzden her madde alıntıyla kanıtlanır ve şüphe `needs_review` ile görünür kılınır. Her iki durum da issue olarak bildirilmeye değer. |
| Hukuki güven | Çıktı **hukuki tavsiye değildir**. Araç, "ne yapmalıyım?" sorusunu değil, "metinde hangi cümleler hangi tür yükümlülüğe karşılık geliyor?" sorusunu cevaplar. Hukuki yorum ve karar kullanıcıya (yetkin bir hukukçuya) aittir. |
| Gizli bilgiler | Araç **hiçbir kimlik bilgisi istemez ve saklamaz**; `.env` gibi dosyalara ihtiyaç duymaz. Belge içeriği diske yazılmaz (rapor çıktıları kullanıcının kendi verdiği `--report`/`--csv` hedefine gider). |
| Girdi dosyaları | Belgeler kullanıcı girdisidir ve **yalnızca metin olarak okunur**. Kod yürütme, `eval`/`exec`, şablon yürütme veya dahili bir yorumlayıcı yoktur; belge içeriği hiçbir zaman komut olarak çalıştırılmaz. |
| Ağ ve dış yazma yok | Uzaktan gelen bir yanıt kod yürütme yoluna giremez; araç dış takip sistemine, e-posta kutusuna veya belge deposuna yazmaz. |
| Kaynak tüketimi | Çıkarım belge uzunluğuyla doğrusaldır; bilinen üstel desen yoktur. `--max-items` çıktı hacmini sınırlar. |
| Alıntı bütünlüğü | Her maddenin alıntısı kaynağa karşı `verify` ile kanıtlanır. Alıntı gösterilemiyorsa madde **çıkarılmaz**; çıktı, doğrulanamayan bir iddia taşımaz. |

## Kapsam dışı

- Kullanıcının verdiği belgenin içeriğinin hukuki doğruluğu veya yeterliliği (bu bir hukuk sorusudur,
  güvenlik değil).
- Belgeden çıkarılan maddelerin hukuki sonuçları ve yorumu.
- Harici bir sistemin bağımsız güvenliği (bu depo değil, onu çağıran kurulum).
