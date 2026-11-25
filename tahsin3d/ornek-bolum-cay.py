"""ÖRNEK BÖLÜM: "Ya çay hiç soğumasaydı?" (01) — 3D motorla.
Yeni bölüm yazarken bunu kopyala, mekânları/olayları konuya göre değiştir.

Çalıştır:  python3 ornek-bolum-cay.py <proje_klasoru> [--kontak] [--render] [--kare N]
  proje_klasoru/work/voice.wav  ve  proje_klasoru/work/phrases.json  (zamanla.py çıktısı) gerekli.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from motor import *

P = os.path.abspath(sys.argv[1]); W = os.path.join(P, "work")
PH = json.load(open(os.path.join(W, "phrases.json")))
SES = os.path.join(W, "voice.wav")
SURE = PH[-1]["e"] + 1.2
def b(i): return sn(PH[i]["s"])        # i. cümlenin başladığı kare
def e(i): return sn(PH[i]["e"])

yeni_sahne(SURE)

# ---- MEKÂNLAR (her biri ayrı x'te; kamera aralarında keser) ----
A, B, C, D = 0, 20, 40, 60
mekan_ic(A, "krem", "karo")                       # Tahsin'in atölyesi/mutfağı
masa(A + 0.9, 0.7); bardak(A + 0.9, 0.55, 0.79)
kutu_esya(A - 1.6, 0.9, 0, 0.5, "#4f7cac"); kutu_esya(A - 1.6, 0.9, 0.5, 0.35, "#d9a441")
mekan_ic(B, "tugla", "ahsap")                     # kahvehane
masa(B + 0.2, 0.9, gen=1.8); tabela(B, 1.15, 2.9, "KAHVE", "#7a3b1d")
for dx in (-0.4, 0.2, 0.8): bardak(B + dx, 0.75, 0.79)
mekan_dis(C, "asfalt", gok=("#1d2b4f", "#3b4f80"), gunes=False)   # gece mahalle, kış
for i, bx in enumerate((-3.2, 3.0)): bina(C + bx, 2.6, renk=("#c98d5a", "#9fb4c7")[i])
for k in range(14): kure("kar", (C - 3 + k * 0.45, -0.5 + (k % 3) * 0.4, 0.02), (0.18, 0.18, 0.05), mat("#ffffff", 0.8, sss=0.2))
mekan_ic(D, "lacivert", "ahsap", isik_guc=0.9)    # bilgi kartı stüdyosu

# ---- KARAKTERLER ----
t = karakter("tahsin", x=A)
anne = karakter("anne", x=B - 1.4, sac="topuz", sac_renk="#5b3a1e", gomlek="#d35d6e", sort="#3d4f7a", kravat="#d35d6e", gozluk=False, boy=0.95)
amca = karakter("amca", x=B + 1.5, sac="kel", gomlek="#8aa1b8", sort="#4a4a4a", kravat="#6b4f3a", gozluk=False, boy=1.0)
komsu = karakter("komsu", x=B + 0.1, y=0.25, sac="kep", sac_renk="#2f6f9f", gomlek="#f0c419", sort="#2f6f9f", kravat="#f0c419", gozluk=False, boy=0.9)

# ---- YAZILAR ----
baslik = yazi("Ya çay hiç\nsoğumasaydı?", (A, -0.8, 3.4), boy=0.27, renk="#ffcc33", emit=0.4)
gorunur(baslik, [(1, True), (e(0) + 6, False)])
bilgi = yazi("Türkiye: kişi başı\nyılda 3+ kg çay", (D - 0.1, -0.4, 3.3), boy=0.26, renk="#ffffff", emit=0.5)
gorunur(bilgi, [(1, False), (b(19), True)]); zipla_belir(bilgi, b(19))
soru = yazi("Sen olsan\nne yapardın?", (D - 0.1, -0.6, 3.3), boy=0.27, renk="#ffcc33", emit=0.4)
gorunur(soru, [(1, False), (b(22), True)]); gorunur(bilgi, [(b(22), False)]); zipla_belir(soru, b(22))

# ---- OYUN (cümle cümle) ----
t.ifade(1, "sasirmis"); t.poz(1, "sasir", gecis=0)                       # 0: Ya çay hiç soğumasaydı?
t.ifade(b(1), "gulumse"); t.poz(b(1), "el_salla")                        # 1: Tuhaf Tahsin bir sabah,
t.poz(b(2), "tut"); t.ifade(b(2) + 20, "mutlu")                          # 2: ... bardak icat etti
t.isinlan(b(3), B - 0.6, -0.4); t.poz(b(3), "sevin"); t.ifade(b(3), "mutlu")   # 3: Önce herkes bayıldı.
for c in (anne, amca, komsu): c.ifade(1, "mutlu"); c.poz(b(3), "sevin")
t.poz(b(7), "dusun"); t.ifade(b(7), "dusunceli")                         # 7: Ama çay gerçekten hiç soğumuyordu.
for c in (anne, amca, komsu): c.poz(b(8), "tut"); c.ifade(b(8), "duz")   # 8-11: üflediler, beklediler, buz attılar, nafile
for c in (anne, amca, komsu): c.ifade(b(12), "korkmus"); c.poz(b(12), "korku"); c.zipla(b(12) + 4, 0.2)   # 12: dili yandı
t.ifade(b(12), "sasirmis"); t.poz(b(12), "sasir")
amca.ifade(b(14), "kizgin"); amca.poz(b(14), "kizgin"); amca.yuru(b(14) + 4, e(14), B + 3.5)            # 14: Çaycı Rıza kapattı
t.ifade(b(15), "uzgun"); t.poz(b(15), "uzgun")                           # 15: Tahsin toplamaya karar verdi
t.isinlan(b(16), C, 0); t.ifade(b(16), "sasirmis"); t.poz(b(16), "korku")    # 16: tam o gece kış geldi
t.poz(b(17), "anlat"); t.ifade(b(17), "gulumse")                         # 17-18: bardaklar evlere, soba yok
t.poz(b(18), "fikir"); t.ifade(b(18), "mutlu")
t.isinlan(b(19), D - 0.55, 0); t.poz(b(19), "isaret_sag"); t.ifade(b(19), "gulumse")   # 19-21: Gerçekte...
t.poz(b(22), "omuz_silk"); t.ifade(b(22), "dusunceli")                   # 22: Peki sen olsan?
t.nefes(1, sn(SURE)); [c.nefes(1, sn(SURE)) for c in (anne, amca, komsu)]
t.konus(SES, 0, SURE)                                                    # anlatıcı = Tahsin

# ---- KAMERA (her mekân geniş açılışla başlar) ----
kamera_cek(1, "orta", t, z_hedef=2.0); kamera_it(1, b(1), 0.8)
kamera_cek(b(1), "genis", t, aci=-12); kamera_cek(b(2), "yakin", t, aci=10)
kamera_cek(b(3), "genis", (B, 0)); kamera_cek(b(4), "orta", anne); kamera_cek(b(5), "orta", komsu); kamera_cek(b(6), "orta", amca)
kamera_cek(b(7), "yakin", t); kamera_cek(b(8), "orta", (B, 0), aci=15)
kamera_cek(b(12), "genis", (B, 0)); kamera_it(b(12), e(13), 0.85)
kamera_cek(b(14), "orta", amca, aci=-10); kamera_cek(b(15), "yakin", t, aci=12)
kamera_cek(b(16), "genis", (C, 0)); kamera_cek(b(17), "orta", t, aci=-15); kamera_cek(b(18), "yakin", t)
kamera_cek(b(19), "orta", (D - 0.1, 0), z_hedef=2.3); kamera_cek(b(22), "orta", (D - 0.1, 0), aci=8, z_hedef=2.3); kamera_it(b(22), sn(SURE), 0.9)

if "--kaydet" in sys.argv: kaydet(os.path.join(W, "sahne.blend"))
if "--kare" in sys.argv:
    for k in sys.argv[sys.argv.index("--kare") + 1].split(","): kare_al(os.path.join(W, f"kare_{int(k):04d}.png"), int(k))
if "--kontak" in sys.argv:
    ks = [b(i) + 6 for i in range(len(PH))]
    for k in ks: kare_al(os.path.join(W, "kontak", f"k_{k:04d}.png"), k)
if "--render" in sys.argv:
    a = sys.argv[sys.argv.index("--render") + 1] if len(sys.argv) > sys.argv.index("--render") + 1 and "-" in sys.argv[sys.argv.index("--render") + 1] else None
    render_et(os.path.join(W, "kareler"), *(map(int, a.split("-")) if a else ()))
