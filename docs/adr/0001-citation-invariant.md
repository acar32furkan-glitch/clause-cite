# ADR-0001 — Her madde birebir alıntı + satır aralığı taşır (alıntı invariyantı)

- **Durum:** Kabul edildi
- **Tarih:** 2026-10-06

## Bağlam

Bir sözleşmeden, yönetmelikten veya şartnameden "aksiyon maddeleri" çıkarmak iki farklı iş olarak
yapılabilir:

1. **Özet tabanlı çıkarım.** Bir dil modeli belgeyi okuyup maddeleri *kendi cümleleriyle* yazar:
   "Tedarikçi 30 gün içinde teslim etmeli, gecikirse ceza öder." Bu akıcıdır ama **kaynağa bağlı
   değildir**. Cümlenin nereden geldiği, aktarımın doğru olup olmadığı, hatta belgede gerçekten var
   olup olmadığı doğrulanamaz.
2. **Kanıt tabanlı çıkarım.** Her madde, metindeki birebir cümleye ve konumuna bağlanır.

Bir hukuk/uyum bağlamında (1) tehlikelidir: bir model "30 gün" der ama belgede "45 gün" yazıyorsa,
"doğrulanamayan doğru bir cümle" en yanıltıcı hatadır. Daha kötüsü, halüsinasyon kaynağı **hiç
göstermeden** üretilebilir. Kullanıcı, aracın doğru söylediğini varsaymak zorunda kalırsa aracın
değeri sıfırdır.

## Karar

**Her madde, kaynak metindeki birebir alıntıyı ve `dosya:satır` aralığını taşımak zorundadır.**

```text
Item:
  kind:      obligation
  modality:  must
  quote:     "Tedarikçi, teslimatı 30 gün içinde tamamlamak zorundadır."
  source:
    file:        sozlesme.txt
    line_start:  12
    line_end:    12
```

- **Birebir.** `quote`, kaynaktaki karakterlerdir. Kısaltma, düzeltme, çeviri veya "daha temiz"
  yeniden yazım yoktur. Alıntıda değiştirilen tek şey yoktur; zorunluysa "…" ile kısaltılır ama bu
  açıkça işaretlenir ve satır aralığı genişler.
- **Konum.** `(dosya, line_start, line_end)` alıntının hangi satır(lar)dan geldiğini söyler ve
  makine tarafından doğrulanabilir.
- **Kapı.** `clause-cite verify <dosya...>` bağımsız çalışır: her maddenin alıntısının kaynakta,
  belirtilen satır aralığında **gerçekten** bulunduğunu kanıtlar. Bulunamazsa çıkış kodu `1` olur —
  bu bir uyarı değil, **ihlaldir**.
- **Çıkarılamayan şey çıkarılmaz.** Bir kalıp bir cümleyle eşleşiyor ama alıntıyı/konumu
  üretemiyorsa, o madde **hiç üretilmez**. "Alıntısız madde" diye bir çıktı yoktur.

## Sonuçlar

- **Kazanç — denetlenebilirlik.** Her madde kaynağına tıklanabilir bir referanstır; kullanıcı "doğru
  mu?" sorusunu **kendisi** cevaplayabilir. Rapor, aracın doğruluğunu varsaymayı gerektirmez.
- **Kazanç — halüsinasyon yapısal olarak imkânsız.** Model olmadan çalışan deterministik kalıplar,
  yalnızca metinde **var olan** sinyalleri eşler ve alıntıyı taşımayı zorunlu kılar. Kaynakta
  bulunamayan bir cümle çıktıda bulunamaz.
- **Kazanç — determinizm.** Aynı belge + aynı `--anchor` her zaman aynı maddeleri üretir; bu,
  maddelerin **test edilebilir** (altın set regresyonu) ve CI'da güvenilir olmasını sağlar.
- **Bedel — kapsam.** Açık sinyali olmayan örtük ifadeler ("makul sürede", "uygun şekilde")
  çıkarılmaz; bu bilinçli bir eksikliktir. (Gelecekte LLM **yalnızca ikincil sinyal** olarak
  önerilebilir ama alıntı zorunluluğu onun için de geçerli kalır — bkz. [yol haritası](../roadmap.md),
  v0.4.)
- **Bedel — bölütleme bağımlılığı.** Doğru `dosya:satır` için cümle→satır eşlemesinin tutarlı olması
  gerekir; PDF/DOCX girdisinde bu eşleme sayfa/paragraf konumuna genellenir (v0.2).
- **Kural.** "Bu maddeyi alıntısız da verebilsem" dürtüsü doğduğunda cevap **hayır**dır: alıntı,
  maddenin kendisinin parçasıdır, süsü değil.

## Neden LLM/eval yerine bu yaklaşım?

- **LLM'li çıkarım doğrulanamaz.** "Model %90 doğru" bir ölçüm olabilir ama tek bir maddenin doğru
  olup olmadığını **kanıtlamaz**. Alıntı invariyantı her maddeyi tek tek kanıtlanabilir kılar.
- **Eval, örnek setine bağlıdır.** Bir altın set, bilinen vakaları korur; bilinmeyen bir belgede
  yeni bir hata üretebilir. Alıntı invariyantı ise **her** belgede, bilinmeyen girdiler dâhil,
  geçerlidir ve `verify` ile sürekli denetlenir.
- **İki yaklaşım birbirini dışlamaz.** clause-cite altın seti (`eval`) **invariyantı korumak** için
  kullanır, invariyantın yerine değil. LLM ise ancak alıntıyı taşıyabildiği sürece (v0.4, ikincil
  sinyal) gündeme gelebilir; kapı kararı asla ona bırakılmaz.
