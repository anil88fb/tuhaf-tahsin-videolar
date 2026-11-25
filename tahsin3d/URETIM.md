# Tuhaf Tahsin 3D üretim talimatı

2026-11-25'ten itibaren bütün Tuhaf Tahsin bölümleri bu 3D motorla üretilir (eski 2D cizgi-short render'ı kullanılmaz).
Karakterin görünüşü sabittir: `referans/tahsin-3d-referans.png` (turuncu zikzak saç, yuvarlak gözlük, krem gömlek + yeşil V şerit, yeşil şort, ince koyu bacaklar).
Görünüşü (renk, saç, gözlük, oran) değiştirme; motor bunu zaten referansa göre kurar.

## Dosyalar
| Dosya | Görevi |
|---|---|
| `kurulum.sh` | bpy (Blender 5), çevrimdışı Whisper, earshot. Oturum başına bir kez. |
| `motor.py` | Karakterler, poz/ifade kütüphanesi, dudak senkronu, mekânlar, eşyalar, 3D yazı, kamera, render. |
| `ornek-bolum-cay.py` | Tam örnek bölüm. Yeni bölüm bunun kopyasıyla yazılır. |
| `zamanla.py` | Seslendirmeden `work/words.json` + `work/phrases.json` (çevrimdışı Whisper; NO_WHISPER gerekmez). |
| `bitir.py` | Kareler + ses + müzik + efekt → 1080x1920 MP4, -14 LUFS. |

## Akış (bir bölüm, ~3 saat; en uzun kısım render)

1. `bash $W/tuhaf-tahsin-videolar/tahsin3d/kurulum.sh`
2. **Senaryo: 30-38 sn** (45 sn'yi geçme; her saniye ~3 dk render demek). "Ya ... olsaydı?" ile başla, "Gerçekte ..." bilgisi, "Peki sen olsan ne yapardın?" ile bit. Anlatıcı Tahsin'dir (ağzı sesle oynar).
   Proje: `$W/ya-olsaydi/NN-kisa-ad/` → `script.txt`, `work/voice.wav` (Speko sesini wav'a çevir: `ffmpeg -i ses.mp3 work/voice.wav`).
3. **Zamanlama:** `python3 tahsin3d/zamanla.py work/voice.wav --metin script.txt --cikti work` → cümle listesi ve kare numaraları ekrana basılır. Eşleşme %60'ın altındaysa sesi dinlenmiş metinle (transkript.txt) karşılaştır.
4. **Bölüm betiği:** `cp tahsin3d/ornek-bolum-cay.py $P/bolum.py`; `PH`, `b(i)`, `e(i)` yapısını koru. Değiştirdiklerin:
   - **Mekânlar** (2-4 tane, her biri ayrı x: 0, 20, 40, 60): `mekan_ic(x, duvar, zemin)` (duvar: tugla krem mavi yesil pembe lacivert karo ahsap; zemin: ahsap karo hali) ya da `mekan_dis(x, zemin, gok=(üst, alt), gunes)` (zemin: cim asfalt kum). Konuya uygun eşyalar: `masa sandalye bardak kutu_esya top agac bulut bina tabela kure kutu silindir koni yazi`. Yeni eşyayı bu ilkel parçalardan kur (kil görünümlü `mat("#renk")`).
   - **Karakterler:** Tahsin `karakter("tahsin", x=...)`. Yan karakterler gözlüksüz, farklı saç (`kel topuz kep kivircik at_kuyrugu sapka`) ve renklerle; en fazla 3 yan karakter (her biri render'ı yavaşlatır).
   - **Oyun:** her cümleye bir `poz` + `ifade`: POZLAR = dur el_salla dusun sasir fikir isaret_sag isaret_sol isaret_ileri omuz_silk sevin uzgun kizgin anlat tut korku selam; IFADELER = gulumse duz dusunceli sasirmis mutlu uzgun kizgin korkmus sikkin. Hareket: `zipla`, `yuru`, `isinlan` (mekân değişimi), `bak`, nesneler için `zipla_belir`, `anahtar`, `gorunur`.
   - **Önce bütün `ifade` çağrıları, en sonda `t.konus(SES, 0, SURE)`** (dudak senkronu ifadeleri okur).
   - **Yazılar:** kare 1'de görünen başlık (`yazi("Ya ...\nolsaydı?", (x, -0.8, 3.4), boy=0.27, renk="#ffcc33", emit=0.4)`, kapak karesi budur), "Gerçekte" bilgi kartı ve son soru kartı (bilgi mekânında, Tahsin'in üstünde z≈3.3). Yazı ≤ 2 satır, satır ≤ 18 harf.
   - **Kamera:** her mekân `genis` açılışla başlar; sonra `orta`/`yakin`/`asiri_yakin`/`alttan`/`ustten`, `aci` ile çeşitle. 2-4 sn'de bir kesme. Çekimlerin çoğu genis/orta (mekân görünsün). `kamera_it` ile yavaş itme. Her yeni `kamera_cek` kesmedir.
5. **Kontak sayfası:** `RES=270 SAMPLES=6 python3 bolum.py $P --kontak` (her cümleden 1 kare, ~1 dk) → kareleri döşe ve BAK: kadraj boş mu, yazı saçla çakışıyor mu, yüz kesiliyor mu, karakterler üst üste mi, duvarın üstü görünüyor mu. Düzelt, en fazla 3 tur.
6. **Tam render (arka planda):** `nohup python3 bolum.py $P --render > $P/render.log 2>&1 &` (RES=432, SAMPLES=8 varsayılan; DÜŞÜRME). Kare başı ~8 sn (4 karakterle). Süre tahmini: `sn × 24 × 8 / 60` dk. `ls work/kareler | wc -l` ile 5-10 dk'da bir izle. Oturum koparsa aynı komut kaldığı yerden devam eder (önce sıfır baytlık son kareyi sil).
7. **Ses:** earshot ile 1 müzik + 3-6 efekt (zıplama, geçiş "vuşş", fikir zili, kalabalık, konuya özel ses):
   `earshot make "a light playful music loop" -o work/sfx/muzik.wav` — bölümler arasında müzik tarifini değiştir (muted guitar, marimba, 8-bit, warm...).
   `work/ses.json`: `{"muzik": "work/sfx/muzik.wav", "muzik_seviye": 0.2, "efektler": [{"dosya": "work/sfx/boing.wav", "sn": 12.4, "seviye": 0.8, "sure": 1.5}]}`. Konuşma her zaman müzikten net duyulmalı.
8. **Bitir:** `python3 tahsin3d/bitir.py $P $P/final.mp4` → sonra kalite kontrolü: süre = ses süresi, 1080x1920, ilk kare başlığı gösteriyor, 6 karelik bir şerit (`ffmpeg -vf "select='not(mod(n\,96))',scale=270:480,tile=6x1"`) ile son kontrol. Dosya < 40 MB olmalı (genelde 5-15 MB).

## Kurallar
- Her bölümde en az 2 farklı mekân, mekânlar bölümden bölüme değişir (durum.md'deki son mekânlara bak).
- Tahsin her sahnede görünür; yan karakterler konuya göre (anne, komşu, öğretmen, satıcı...).
- Sahneler "kil animasyonu / oyuncak" sıcaklığında: sıcak ışık, yumuşak gölge. Karanlık sahnede bile karakterin yüzü okunur olmalı.
- Render ayarlarını (RES 432, SAMPLES 8, BOUNCES 2, 24 fps) düşürme; süre yetmiyorsa senaryoyu kısalt ya da yan karakter sayısını azalt.
