"""BÖLÜM 07: "Ya bulutlar pamuk şeker olsaydı?" — 3D motor. Mekânlar: sahil (gündüz), pembe gökli sahil/dondurma tezgâhı, bilgi stüdyosu."""
import json, os, sys, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from motor import *
from motor import _fcurves

P = os.path.abspath(sys.argv[1]); W = os.path.join(P, "work")
PH = json.load(open(os.path.join(W, "phrases.json")))
SES = os.path.join(W, "voice.wav")
SURE = PH[-1]["e"] + 1.2
def b(i): return sn(PH[i]["s"])
def e(i): return sn(PH[i]["e"])

yeni_sahne(SURE)
random.seed(7)
A, B, C = 0, 20, 40

def deniz(x):
    kutu("deniz", (x, 2.9, 0.02), (8, 1.6, 0.06), mat("#2f8fc4", 0.15, sss=0.05), bevel=0)
    for k in range(6): kutu("kopuk", (x - 6 + k * 2.4, 1.32, 0.05), (0.7, 0.05, 0.04), mat("#ffffff", 0.6), bevel=0.02)

def bulut_m(x, y, z, olcek, m):
    for dx, r in [(-0.35, 0.3), (0, 0.42), (0.38, 0.32), (0.15, 0.3)]:
        kure("bulut", (x + dx * olcek, y, z + (0.1 if r > 0.4 else 0) * olcek), (r * olcek, r * olcek * 0.8, r * olcek * 0.7), m)

def semsiye(x, y, renk):
    silindir("semsiye_sap", (x, y, 0), (x, y, 1.9), 0.03, mat("#f2f2f2", 0.4), uclar=False)
    koni("semsiye", (x, y, 1.95), 0.9, 0.05, 0.35, mat(renk, 0.5))

def marti(x, y, z, pembe=False):
    g = mat("#f4f4f4", 0.6); x0 = x; y0 = y
    kure("marti_govde", (x, y, z + 0.18), (0.2, 0.12, 0.12), g); kure("marti_kafa", (x - 0.2, y, z + 0.3), (0.08, 0.08, 0.08), g)
    koni("marti_gaga", (x - 0.31, y, z + 0.3), 0.025, 0.0, 0.1, mat("#f2b632", 0.4), rot=(0, -90, 0))
    for s in (-1, 1): kutu("marti_kanat", (x + 0.03, y + s * 0.12, z + 0.22), (0.16, 0.04, 0.02), g, rot=(s * 12, 0, 0))
    if pembe:
        for k in range(3): kure("seker_damla", (x - 0.05 + k * 0.08, y - 0.1, z + 0.28), (0.05, 0.05, 0.04), mat("#ff8fc8", 0.25, sss=0.1))

# ---- MEKÂN A: sahil gündüz + makine ----
mekan_dis(A, "kum", gok=("#5fb8f0", "#cdeeff"), gunes=True)
deniz(A); semsiye(A - 2.4, 0.9, "#e94f4f")
bm = bpy.data.materials.new("bulut_A"); bm.use_nodes = True; bb = bm.node_tree.nodes["Principled BSDF"]
bb.inputs["Roughness"].default_value = 0.9; bb.inputs["Subsurface Weight"].default_value = 0.2
bulut_m(A - 2.2, 3.6, 4.0, 1.3, bm); bulut_m(A + 1.8, 3.6, 4.6, 1.5, bm); bulut_m(A + 0.0, 3.6, 3.2, 0.9, bm)
inp = bb.inputs["Base Color"]
for k, c in [(1, "#ffffff"), (b(4) + 4, "#ffffff"), (b(4) + 22, "#ff9ad0"), (b(12) - 4, "#ff9ad0"), (b(12) + 20, "#ffffff")]:
    inp.default_value = (*srgb(c), 1); inp.keyframe_insert("default_value", frame=k)
# makine
MX = A + 1.25
kutu("makine", (MX, 0.35, 0.45), (0.42, 0.34, 0.45), mat("#3bb3a6", 0.45))
kutu("makine_bant", (MX, 0.0, 0.62), (0.43, 0.02, 0.07), mat("#ff7eb6", 0.4), bevel=0.01)
for k, rr in enumerate(("#ffd54a", "#e94f4f", "#ffffff")): kure("dugme", (MX - 0.2 + k * 0.2, -0.0, 0.35), (0.05, 0.03, 0.05), mat(rr, 0.3, emit=0.3))
silindir("boru", (MX, 0.35, 0.9), (MX, 0.35, 2.3), 0.09, mat("#c9ccd1", 0.3, metal=0.5))
koni("huni", (MX, 0.35, 2.45), 0.12, 0.32, 0.35, mat("#ff7eb6", 0.4))
kranky = bos("krank", (MX + 0.44, 0.35, 0.55))
silindir("krank_kol", (MX + 0.46, 0.35, 0.55), (MX + 0.6, 0.35, 0.55), 0.03, mat("#555555", 0.3), parent=kranky, uclar=False)
silindir("krank_sap", (MX + 0.6, 0.35, 0.55), (MX + 0.6, 0.35, 0.85), 0.035, mat("#e94f4f", 0.4), parent=kranky)
for k, r in [(1, 0), (b(3), 0), (b(3) + 20, 360), (b(4) + 10, 720), (b(11) + 2, 720), (b(11) + 22, 0)]: anahtar(kranky, k, rot=(r, 0, 0))
duman = []
for k in range(5):
    d = kure("pembe_duman", (MX + random.uniform(-0.25, 0.25), 0.35, 2.7 + k * 0.32), (1, 0.9, 0.8), mat("#ffb3da", 0.9, sss=0.2))
    gorunur(d, [(1, False), (b(4) + k * 3, True), (e(4) + 6, False)]); zipla_belir(d, b(4) + k * 3, son=0.2)

# ---- MEKÂN B: pembe gök, sahil + dondurma tezgâhı ----
mekan_dis(B, "kum", gok=("#ff9fd2", "#ffe6f4"), gunes=False)
deniz(B); semsiye(B + 2.6, 0.9, "#4f9fe9")
for (bx, bz, o) in [(-2.4, 4.3, 1.4), (1.6, 4.8, 1.6), (0.2, 3.4, 1.0), (3.4, 3.6, 1.1)]: bulut_m(B + bx, 3.6, bz, o, mat("#ff9ad0", 0.9, sss=0.2))
kutu("tezgah", (B + 1.5, 0.7, 0.5), (0.65, 0.35, 0.5), mat("#f7f1e3", 0.5))
kutu("tezgah_serit", (B + 1.5, 0.34, 0.7), (0.66, 0.02, 0.12), mat("#e94f4f", 0.5), bevel=0.01)
for k in range(3): koni("tente", (B + 1.0 + k * 0.5, 0.6, 1.75), 0.28, 0.0, 0.25, mat(("#e94f4f", "#ffffff", "#e94f4f")[k], 0.5))
silindir("tente_dir", (B + 0.9, 0.4, 1.0), (B + 0.9, 0.4, 1.62), 0.025, mat("#f2f2f2"), uclar=False)
silindir("tente_dir", (B + 2.1, 0.4, 1.0), (B + 2.1, 0.4, 1.62), 0.025, mat("#f2f2f2"), uclar=False)
tabela(B + 1.5, 0.3, 1.38, "DONDURMA", "#e94f4f", "#ffffff", gen=1.2, yuk=0.28)
for k, c in enumerate(("#ffd54a", "#ff9ad0", "#8fd16a")):
    koni("kulah", (B + 1.15 + k * 0.35, 0.5, 1.07), 0.0, 0.06, 0.16, mat("#d9a441", 0.6), rot=(0, 0, 0))
    kure("top", (B + 1.15 + k * 0.35, 0.5, 1.2), (0.07, 0.07, 0.07), mat(c, 0.35, sss=0.1))
marti(B - 2.4, -0.2, 0, True); marti(B - 3.1, 0.4, 0, True)
# şeker yağmuru: kolon halinde damlalar, ebeveyn aşağı kayar
yag = bos("yagmur", (B, 0, 0))
for k in range(120):
    d = kure("seker_damla", (B + random.uniform(-3.5, 3.5), random.uniform(-1.8, 1.6), random.uniform(0.3, 14)), (0.075, 0.075, 0.13), mat("#ff8fc8", 0.25, sss=0.1), parent=yag, seg=12)
    gorunur(d, [(1, False), (b(7) + 8, True), (b(11), False)])
anahtar(yag, b(7) + 8, loc=(B, 0, 0)); anahtar(yag, b(11), loc=(B, 0, -12))
for fc in _fcurves(yag):
    for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
# yapışkan şeker birikintileri
for (px, py, r) in [(-1.2, -0.3, 0.35), (0.9, -0.6, 0.3), (-0.2, 0.6, 0.4), (2.4, -0.2, 0.3)]:
    p_ = kure("seker_birikinti", (B + px, py, 0.0), (r, r * 0.8, 0.04), mat("#ff8fc8", 0.2, sss=0.1))
    gorunur(p_, [(1, False), (b(9), True)])

# ---- MEKÂN C: bilgi stüdyosu ----
mekan_ic(C, "mavi", "ahsap", isik_guc=0.95)
bulut_m(C + 1.3, 0.8, 1.2, 1.1, mat("#ffffff", 0.9, sss=0.2))
tabela(C + 1.3, 0.75, 0.35, "~500 TON SU", "#2f6fa8", "#ffffff", gen=1.6, yuk=0.32)
for k in range(4): kure("damla", (C + 0.85 + k * 0.3, 0.8, 0.75 - (k % 2) * 0.12), (0.05, 0.05, 0.08), mat("#5fb8f0", 0.15, sss=0.1))

# ---- KARAKTERLER ----
t = karakter("tahsin", x=A)
cocuk = karakter("cocuk", x=B - 1.3, y=-0.1, sac="kivircik", sac_renk="#3b2a1a", gomlek="#ffd54a", sort="#3d6fb5", kravat="#ffd54a", gozluk=False, boy=0.78)
hasan = karakter("hasan", x=B + 1.5, y=0.0, sac="sapka", sac_renk="#ffffff", gomlek="#ffffff", sort="#e94f4f", kravat="#e94f4f", gozluk=False, boy=1.0)

# ---- YAZILAR ----
baslik = yazi("Ya bulutlar pamuk\nşeker olsaydı?", (A, -0.8, 3.3), boy=0.19, renk="#ffcc33", emit=0.4)
gorunur(baslik, [(1, True), (e(0) + 8, False)])
bilgi = yazi("Bir bulut\n≈ 500 ton su!", (C - 0.1, -0.4, 3.3), boy=0.26, renk="#ffffff", emit=0.5)
gorunur(bilgi, [(1, False), (b(13), True)]); zipla_belir(bilgi, b(13))
soru = yazi("Sen olsan\nne yapardın?", (C - 0.1, -0.6, 3.3), boy=0.27, renk="#ffcc33", emit=0.4)
gorunur(soru, [(1, False), (b(16), True)]); gorunur(bilgi, [(b(16), False)]); zipla_belir(soru, b(16))

# ---- OYUN ----
t.ifade(1, "sasirmis"); t.poz(1, "sasir", gecis=0)                                  # 0 Ya bulutlar...
t.ifade(b(1), "gulumse"); t.poz(b(1), "anlat")                                     # 1 makine kurdu
t.poz(b(2), "isaret_sag"); t.ifade(b(2), "mutlu")                                  # 2 adını koydu
t.yuru(b(3) - 14, b(3) + 4, A + 0.55); t.poz(b(3) + 8, "tut"); t.ifade(b(3), "dusunceli")   # 3 kolu çevirdi
t.poz(b(4) + 16, "sasir"); t.ifade(b(4) + 16, "sasirmis"); t.bak(b(4) + 20, -10)   # 4 bulutlar pembeleşti
t.isinlan(b(5), B - 0.2, -0.3); t.poz(b(5), "sevin"); t.ifade(b(5), "mutlu"); t.bak(b(5), 0)   # 5 çocuklar zıpladı
cocuk.ifade(1, "mutlu"); cocuk.poz(1, "sevin", gecis=0); hasan.ifade(1, "gulumse"); hasan.poz(1, "tut", gecis=0)
for k in (b(5) + 4, b(5) + 24): cocuk.zipla(k, 0.4)
hasan.ifade(b(6), "mutlu"); hasan.poz(b(6), "sevin"); hasan.yuru(b(6) + 6, e(6), B + 0.7, -0.2)   # 6 Hasan tezgâhı bıraktı
t.poz(b(7), "dusun"); t.ifade(b(7), "dusunceli"); t.bak(b(7), 0)                   # 7 yağmur başladı
for c in (cocuk, hasan): c.poz(b(7) + 4, "dur"); c.ifade(b(7) + 4, "sasirmis")
t.poz(b(8), "korku"); t.ifade(b(8), "korkmus")                                     # 8 şeker yağmuru
for c in (cocuk, hasan): c.poz(b(8) + 3, "korku"); c.ifade(b(8) + 3, "korkmus")
for c in (t, cocuk, hasan): c.poz(b(9), "uzgun"); c.ifade(b(9), "sikkin")          # 9 yapış yapış
hasan.poz(b(10), "isaret_sol"); hasan.ifade(b(10), "uzgun")                        # 10 martılar
t.isinlan(b(11), A + 0.55, 0); t.poz(b(11), "tut"); t.ifade(b(11), "kizgin")      # 11 kolu geri çevirdi
t.poz(b(12) + 6, "sevin"); t.ifade(b(12) + 6, "mutlu")                            # 12 bembeyaz
t.isinlan(b(13), C - 0.6, 0); t.poz(b(13), "isaret_sag"); t.ifade(b(13), "gulumse")   # 13 Gerçekte...
t.poz(b(14), "anlat"); t.ifade(b(14), "sasirmis")                                  # 14-15 bütün sahil
t.poz(b(15), "omuz_silk"); t.ifade(b(15), "gulumse")
t.poz(b(16), "omuz_silk"); t.ifade(b(16), "dusunceli")                             # 16 soru
t.nefes(1, sn(SURE)); cocuk.nefes(1, sn(SURE)); hasan.nefes(1, sn(SURE))
t.konus(SES, 0, SURE)

# ---- KAMERA ----
kamera_cek(1, "orta", t, z_hedef=2.0); kamera_it(1, b(1), 0.85)
kamera_cek(b(1), "genis", (A + 0.5, 0), aci=-12)
kamera_cek(b(2), "orta", (A + 0.7, 0), aci=12, z_hedef=1.7)
kamera_cek(b(3), "orta", (A + 0.85, 0), aci=22, z_hedef=1.6)
kamera_cek(b(4), "genis", (A + 0.6, 0), aci=-8, z_hedef=2.4); kamera_it(b(4), e(4), 0.9)
kamera_cek(b(5), "genis", (B, 0))
kamera_cek(b(6), "orta", hasan, aci=-12)
kamera_cek(b(7), "genis", (B, 0), aci=10); kamera_it(b(7), e(8), 0.85)
kamera_cek(b(9), "orta", t, aci=12)
kamera_cek(b(10), "alttan", (B - 2.7, 0.3), aci=-10, z_hedef=0.5)
kamera_cek(b(11), "orta", (A + 0.75, 0), aci=-18, z_hedef=1.7)
kamera_cek(b(12), "genis", (A + 0.4, 0), aci=8)
kamera_cek(b(13), "orta", (C - 0.1, 0), z_hedef=2.3)
kamera_cek(b(15), "orta", (C - 0.3, 0), aci=-14, z_hedef=2.2)
kamera_cek(b(16), "orta", (C - 0.1, 0), aci=8, z_hedef=2.3); kamera_it(b(16), sn(SURE), 0.9)

if "--kare" in sys.argv:
    for k in sys.argv[sys.argv.index("--kare") + 1].split(","): kare_al(os.path.join(W, f"kare_{int(k):04d}.png"), int(k))
if "--kontak" in sys.argv:
    ks = [b(i) + 8 for i in range(len(PH))]
    for k in ks: kare_al(os.path.join(W, "kontak", f"k_{k:04d}.png"), k)
if "--render" in sys.argv:
    render_et(os.path.join(W, "kareler"))
