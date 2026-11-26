"""BÖLÜM 07 (v2): "Ya bulutlar pamuk şeker olsaydı?" — 3D motor. Dolu sahil, geniş çekimler, yazılar 2D katmanda (altyazi.py)."""
import json, os, sys, random, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import motor
from motor import *
from motor import _fcurves

P = os.path.abspath(sys.argv[1]); W = os.path.join(P, "work")
PH = json.load(open(os.path.join(W, "phrases.json")))
SES = os.path.join(W, "voice.wav")
SURE = PH[-1]["e"] + 1.2
def b(i): return sn(PH[i]["s"])
def e(i): return sn(PH[i]["e"])
SON = sn(SURE)
motor.CEKIMLER["cok_genis"] = (9.5, 2.5, 28)

yeni_sahne(SURE, arka="#cfe9ff")
random.seed(7)
A, B, C = 0, 20, 40
R = random.uniform

def lineer(o):
    for fc in _fcurves(o):
        for kp in fc.keyframe_points: kp.interpolation = "LINEAR"

def sallan(o, k0, k1, eksen=1, aci=4, periyot=40, faz=0):
    """rotasyon salınımı (tekne, şemsiye...)"""
    r0 = [math.degrees(a) for a in o.rotation_euler]
    for k in range(k0, k1 + 1, periyot // 2):
        r = list(r0); r[eksen] += aci * (1 if ((k - k0) // (periyot // 2) + faz) % 2 == 0 else -1)
        anahtar(o, k, rot=r)

def grup(ad, loc): return bos(ad, loc)

# ---------- ortak sahil dekoru ----------
def kum_zemin(x):
    o = bpy.data.objects[f"zemin_{x}"]; o.scale = (19.9, 34, 1); o.location.y = -8

def deniz(x):
    kutu("deniz", (x, 3.1, 0.02), (16, 1.5, 0.06), mat("#2f8fc4", 0.15, sss=0.05), bevel=0)
    for k in range(9):
        g = grup("dalga", (x - 9 + k * 2.3, 1.62, 0.07))
        kutu("kopuk", (x - 9 + k * 2.3, 1.62, 0.07), (0.6, 0.05, 0.035), mat("#ffffff", 0.6), parent=g, bevel=0.02)
        for kk in range(1, SON, 36):
            anahtar(g, kk, loc=(x - 9 + k * 2.3 + (0.25 if (kk // 36 + k) % 2 else -0.25), 1.62 + (0.08 if (kk // 36) % 2 else 0), 0.07))

def tepe(x, y, z, sx, sz, renk): kure("tepe", (x, y, z), (sx, 0.5, sz), mat(renk, 0.8))

def tekne(x, y, renk, yelken="#ffffff"):
    g = grup("tekne", (x, y, 0.08))
    kutu("govde", (x, y, 0.12), (0.45, 0.16, 0.1), mat(renk, 0.5), parent=g, bevel=0.06)
    silindir("direk", (x, y, 0.2), (x, y, 1.0), 0.018, mat("#7a4b2a"), parent=g, uclar=False)
    koni("yelken", (x + 0.15, y, 0.6), 0.28, 0.0, 0.75, mat(yelken, 0.6), parent=g, rot=(90, 0, 90), seg=3)
    sallan(g, 1, SON, eksen=1, aci=5, periyot=48, faz=int(x) % 2)

def iskele(x0, x1, y0=0.4):
    for k in range(int((x1 - x0) / 0.32)):
        kutu("tahta", (x0 + k * 0.32, y0 + 1.2, 0.32), (0.14, 1.3, 0.03), mat("#a8743f" if k % 2 else "#94632f", 0.7), bevel=0.01)
    for k in range(0, int((x1 - x0) / 0.32), 4):
        for dy in (-1.1, 1.1): silindir("kazik", (x0 + k * 0.32, y0 + 1.2 + dy, -0.2), (x0 + k * 0.32, y0 + 1.2 + dy, 0.45), 0.05, mat("#6b4423"), uclar=False)

def palmiye(x, y, boy=2.8, egim=8):
    m = mat("#9a6b3a", 0.7); px, pz = x, 0.0
    for k in range(6):
        nx, nz = px + math.sin(math.radians(egim)) * boy / 6 * (1 + k * 0.15), pz + boy / 6
        silindir("palmiye_govde", (px, y, pz), (nx, y, nz), 0.09 - k * 0.008, m, uclar=k == 5); px, pz = nx, nz
    g = grup("yapraklar", (px, y, pz))
    for a in range(0, 360, 60):
        r = math.radians(a)
        kure("palmiye_yaprak", (px + math.cos(r) * 0.55, y + math.sin(r) * 0.3, pz - 0.15), (0.65, 0.16, 0.05), mat("#3f9a3a", 0.6, sss=0.05), parent=g)
        bpy.context.object.rotation_euler = (0, math.radians(18), r)
    sallan(g, 1, SON, eksen=1, aci=3, periyot=60)

def semsiye(x, y, renk, renk2="#ffffff"):
    g = grup("semsiye", (x, y, 0))
    silindir("semsiye_sap", (x, y, 0), (x, y, 1.9), 0.03, mat("#f2f2f2", 0.4), parent=g, uclar=False)
    koni("semsiye", (x, y, 1.95), 0.9, 0.05, 0.35, mat(renk, 0.5), parent=g, seg=8)
    kure("semsiye_tepe", (x, y, 2.14), (0.06, 0.06, 0.06), mat(renk2), parent=g)
    return g

def havlu(x, y, r1, r2, rot=0):
    for k in range(4): kutu("havlu", (x - 0.3 + k * 0.2, y, 0.012), (0.1, 0.55, 0.012), mat(r1 if k % 2 else r2, 0.8), bevel=0, rot=(0, 0, 0))

def kale(x, y):
    m = mat("#d9b26f", 0.9)
    kutu("kale", (x, y, 0.14), (0.3, 0.22, 0.14), m, bevel=0.03)
    for dx in (-0.28, 0.28):
        silindir("kule", (x + dx, y, 0), (x + dx, y, 0.42), 0.1, m, uclar=False); koni("kule_ucu", (x + dx, y, 0.5), 0.12, 0.0, 0.18, m)
    silindir("bayrak_dir", (x, y, 0.28), (x, y, 0.6), 0.008, mat("#ffffff"), uclar=False)
    kutu("bayrak", (x + 0.07, y, 0.56), (0.07, 0.005, 0.04), mat("#e94f4f"), bevel=0)

def kova(x, y, renk):
    koni("kova", (x, y, 0.12), 0.1, 0.13, 0.24, mat(renk, 0.4)); halka("kova_sap", (x, y, 0.25), 0.11, 0.008, mat("#333333"), rot=(90, 0, 0), yarim="ust")
    kutu("kurek", (x + 0.22, y - 0.05, 0.02), (0.05, 0.16, 0.012), mat("#ffd54a", 0.4), bevel=0.01, rot=(0, 0, 30))

def deniz_yildizi(x, y, renk="#ff8a5c"):
    for a in range(0, 360, 72):
        r = math.radians(a); kure("yildiz", (x + math.cos(r) * 0.05, y + math.sin(r) * 0.05, 0.015), (0.06, 0.022, 0.015), mat(renk, 0.6))
        bpy.context.object.rotation_euler = (0, 0, r)

def kabuk(x, y, renk="#ffe0d0"): kure("kabuk", (x, y, 0.02), (0.06, 0.05, 0.03), mat(renk, 0.4))

def plaj_topu(x, y, z0=0.16, ziplat=True):
    g = grup("plajtopu", (x, y, z0))
    for k, c in enumerate(("#e94f4f", "#ffffff", "#3d7fe0", "#ffd54a")):
        kure("top_dilim", (x, y, z0), (0.16, 0.16, 0.16), mat(c, 0.35), parent=g, seg=16)
        bpy.context.object.scale = (0.16 - k * 0.001, 0.16 - k * 0.001, 0.16); bpy.context.object.rotation_euler = (0, 0, math.radians(k * 45))
    if ziplat:
        for kk in range(1, SON, 30):
            anahtar(g, kk, loc=(x, y, z0)); anahtar(g, kk + 15, loc=(x, y, z0 + 0.7))
    return g

def cankurtaran(x, y):
    m = mat("#ffffff", 0.5)
    for dx in (-0.35, 0.35):
        for dy in (-0.3, 0.3): silindir("kule_ayak", (x + dx, y + dy, 0), (x + dx * 0.7, y + dy * 0.7, 1.3), 0.04, m, uclar=False)
    kutu("kule_kabin", (x, y, 1.5), (0.4, 0.35, 0.22), mat("#e94f4f", 0.5)); koni("kule_cati", (x, y, 1.95), 0.6, 0.0, 0.35, mat("#ffffff"), seg=4)
    halka("simit", (x, y - 0.37, 1.5), 0.13, 0.04, mat("#ff7a3d", 0.4), rot=(90, 0, 0))

def figur(x, y, gomlek, sac="#3b2a1a", yatik=False, sapka=None):
    """Arka plan figürü (ucuz): gövde + kafa."""
    g = grup("figur", (x, y, 0)); ten = mat("#e3b98f", 0.6, sss=0.1)
    if yatik:
        kure("figur_govde", (x, y, 0.14), (0.42, 0.16, 0.12), mat(gomlek, 0.6), parent=g); kure("figur_kafa", (x - 0.5, y, 0.15), (0.13, 0.13, 0.13), ten, parent=g)
        kure("figur_sac", (x - 0.55, y, 0.18), (0.11, 0.13, 0.12), mat(sac, 0.5), parent=g)
    else:
        silindir("figur_bacak", (x - 0.06, y, 0), (x - 0.06, y, 0.5), 0.035, mat("#3c3a2c"), parent=g); silindir("figur_bacak", (x + 0.06, y, 0), (x + 0.06, y, 0.5), 0.035, mat("#3c3a2c"), parent=g)
        kure("figur_govde", (x, y, 0.72), (0.18, 0.14, 0.26), mat(gomlek, 0.6), parent=g); kure("figur_kafa", (x, y, 1.12), (0.15, 0.15, 0.15), ten, parent=g)
        kure("figur_sac", (x, y + 0.03, 1.2), (0.15, 0.14, 0.09), mat(sac, 0.5), parent=g)
        if sapka: silindir("figur_sapka", (x, y, 1.24), (x, y, 1.27), 0.24, mat(sapka, 0.5), parent=g, uclar=False)
        for kk in range(1, SON, 24): anahtar(g, kk, loc=(x, y, 0)); anahtar(g, kk + 12, loc=(x, y, 0.05))
    return g

def sahil(x, gok, gunes=True, pembe=False):
    mekan_dis(x, "kum", gok=gok, gunes=gunes); kum_zemin(x); deniz(x)
    gk = bpy.data.objects[f"gok_{x}"]; gk.scale = (19.9, 20, 1); gk.location.z = 9
    tepe(x - 6, 3.85, 0.0, 3.2, 1.3, "#7fae8a"); tepe(x + 5.5, 3.85, 0.0, 3.8, 1.7, "#6f9f80"); tepe(x + 0.5, 3.9, 0.0, 2.6, 0.9, "#8dbb96")
    tekne(x - 2.8, 3.0, "#e94f4f"); tekne(x + 3.6, 3.4, "#3d7fe0", "#ffd54a"); tekne(x + 7.0, 3.6, "#ffffff", "#ff9ad0")
    iskele(x - 7.5, x - 4.5, y0=0.3)
    palmiye(x - 4.2, 1.2, 3.0, 10); palmiye(x + 4.6, 1.4, 2.7, -12); palmiye(x + 6.2, 0.6, 3.2, -6)
    cankurtaran(x + 3.4, 1.6)
    havlu(x - 2.0, 0.9, "#3d7fe0", "#ffffff"); havlu(x + 2.4, -0.6, "#ffd54a", "#e94f4f")
    kale(x - 1.4, -1.3); kova(x - 0.9, -1.6, "#3d7fe0"); kova(x + 1.9, -1.8, "#e94f4f")
    for k in range(8): kabuk(x + R(-4, 4), R(-2.2, 0.8), random.choice(("#ffe0d0", "#fff3c4", "#ffd1e6")))
    deniz_yildizi(x - 2.6, -0.9); deniz_yildizi(x + 0.9, -2.1, "#ffb347")
    figur(x - 5.2, 1.0, "#3d7fe0", yatik=True); figur(x + 5.4, 1.9, "#8fd16a", sapka="#f2d28b"); figur(x - 3.3, 2.2, "#ff7a3d", sac="#d9a441")

# ---------- MEKÂN A: gündüz sahil + makine ----------
sahil(A, ("#5fb8f0", "#cdeeff"))
s1 = semsiye(A - 2.4, 0.7, "#e94f4f"); plaj_topu(A - 3.0, 0.2)
bm = bpy.data.materials.new("bulut_A"); bm.use_nodes = True; bb = bm.node_tree.nodes["Principled BSDF"]
bb.inputs["Roughness"].default_value = 0.9; bb.inputs["Subsurface Weight"].default_value = 0.2
inp = bb.inputs["Base Color"]
for k, c in [(1, "#ffffff"), (b(4) + 4, "#ffffff"), (b(4) + 20, "#ff9ad0"), (b(12) - 4, "#ff9ad0"), (b(12) + 18, "#ffffff")]:
    inp.default_value = (*srgb(c), 1); inp.keyframe_insert("default_value", frame=k)
bulutlar = []
for (bx, bz, o) in [(-3.2, 5.0, 1.6), (2.4, 5.6, 1.9), (-0.4, 4.0, 1.1), (5.0, 4.4, 1.3), (-6.0, 4.6, 1.4)]:
    g = grup("bulutg", (A + bx, 3.7, bz))
    for dx, r in [(-0.35, 0.3), (0, 0.42), (0.38, 0.32), (0.15, 0.3)]:
        kure("bulut", (A + bx + dx * o, 3.7, bz + (0.1 if r > 0.4 else 0) * o), (r * o, r * o * 0.8, r * o * 0.7), bm, parent=g)
    bulutlar.append(g)
    for kk in range(1, SON, 48): anahtar(g, kk, loc=(A + bx + (0.15 if (kk // 48) % 2 else 0), 3.7, bz))
for i, g in enumerate(bulutlar):   # pembeleşirken zıplayıp şişer
    k = b(4) + 8 + i * 3; anahtar(g, k - 1, olcek=1.0); anahtar(g, k + 6, olcek=1.25); anahtar(g, k + 12, olcek=0.95); anahtar(g, k + 18, olcek=1.08)
    k = b(12) + 2 + i * 2; anahtar(g, k, olcek=1.08); anahtar(g, k + 8, olcek=0.9); anahtar(g, k + 16, olcek=1.0)
# makine (ebeveyn: titreme)
MX = A + 1.25
mk = grup("makine_g", (MX, 0.35, 0))
kutu("makine", (MX, 0.35, 0.45), (0.42, 0.34, 0.45), mat("#3bb3a6", 0.45), parent=mk)
kutu("makine_bant", (MX, 0.0, 0.62), (0.43, 0.02, 0.07), mat("#ff7eb6", 0.4), parent=mk, bevel=0.01)
for k, rr in enumerate(("#ffd54a", "#e94f4f", "#ffffff")): kure("dugme", (MX - 0.2 + k * 0.2, -0.0, 0.35), (0.05, 0.03, 0.05), mat(rr, 0.3, emit=0.6), parent=mk)
silindir("boru", (MX, 0.35, 0.9), (MX, 0.35, 2.3), 0.09, mat("#c9ccd1", 0.3, metal=0.5), parent=mk)
koni("huni", (MX, 0.35, 2.45), 0.12, 0.32, 0.35, mat("#ff7eb6", 0.4), parent=mk)
lamba = kure("lamba", (MX - 0.25, 0.35, 0.98), (0.07, 0.07, 0.07), mat("#ff4f9a", 0.3, emit=3.0), parent=mk)
tabela(MX, -0.02, 0.18, "BULUT", "#ff7eb6", "#ffffff", gen=0.7, yuk=0.18)
kr = bos("krank", (MX + 0.44, 0.35, 0.55))
silindir("krank_kol", (MX + 0.46, 0.35, 0.55), (MX + 0.6, 0.35, 0.55), 0.03, mat("#555555", 0.3), parent=kr, uclar=False)
silindir("krank_sap", (MX + 0.6, 0.35, 0.55), (MX + 0.6, 0.35, 0.85), 0.035, mat("#e94f4f", 0.4), parent=kr)
for k, r in [(1, 0), (b(3), 0), (b(3) + 20, 360), (b(4) + 10, 720), (b(11) + 2, 720), (b(11) + 22, 0)]: anahtar(kr, k, rot=(r, 0, 0))
for k in range(b(3) + 4, e(4), 2):   # titreme
    anahtar(mk, k, loc=(MX + R(-0.025, 0.025), 0.35, R(0, 0.04)), olcek=(1.0, 1.0, 1.0 + R(-0.03, 0.05)))
anahtar(mk, e(4) + 2, loc=(MX, 0.35, 0), olcek=1.0)
for k in range(b(11) + 2, b(11) + 24, 2): anahtar(mk, k, loc=(MX + R(-0.02, 0.02), 0.35, R(0, 0.03)))
anahtar(mk, b(11) + 26, loc=(MX, 0.35, 0))
for k in range(14):   # pembe duman: borudan yükselip büyüyen toplar
    d = kure("pembe_duman", (MX, 0.35, 2.6), (1, 1, 1), mat("#ffb3da", 0.9, sss=0.2), seg=16)
    k0 = b(4) - 6 + k * 5; gorunur(d, [(1, False), (k0, True), (k0 + 40, False)])
    anahtar(d, k0, loc=(MX, 0.35, 2.6), olcek=0.05); anahtar(d, k0 + 40, loc=(MX + R(-1.2, 1.2), 0.35 + R(0, 1), 5.2), olcek=R(0.3, 0.5)); lineer(d)

# ---------- MEKÂN B: pembe gökli sahil + dondurma / pamuk şeker tezgâhı ----------
sahil(B, ("#ff9fd2", "#ffe6f4"), gunes=False, pembe=True)
for (bx, bz, o) in [(-3.0, 4.9, 1.6), (2.2, 5.4, 1.9), (-0.2, 3.9, 1.1), (4.6, 4.2, 1.3), (-6.0, 4.4, 1.4)]:
    g = grup("bulutB", (B + bx, 3.7, bz))
    for dx, r in [(-0.35, 0.3), (0, 0.42), (0.38, 0.32), (0.15, 0.3)]:
        kure("bulut", (B + bx + dx * o, 3.7, bz + (0.1 if r > 0.4 else 0) * o), (r * o, r * o * 0.8, r * o * 0.7), mat("#ff9ad0", 0.9, sss=0.2), parent=g)
    for kk in range(1, SON, 40): anahtar(g, kk, olcek=1.0 + (0.06 if (kk // 40) % 2 else 0))
s2 = semsiye(B + 2.9, 0.9, "#4f9fe9"); s3 = semsiye(B - 2.6, 1.1, "#ffd54a", "#e94f4f"); plaj_topu(B - 1.9, 1.4)
kutu("tezgah", (B + 1.5, 0.7, 0.5), (0.65, 0.35, 0.5), mat("#f7f1e3", 0.5))
kutu("tezgah_serit", (B + 1.5, 0.34, 0.7), (0.66, 0.02, 0.12), mat("#e94f4f", 0.5), bevel=0.01)
for k in range(3): koni("tente", (B + 1.0 + k * 0.5, 0.6, 1.75), 0.28, 0.0, 0.25, mat(("#e94f4f", "#ffffff", "#e94f4f")[k], 0.5))
for dx in (0.9, 2.1): silindir("tente_dir", (B + dx, 0.4, 1.0), (B + dx, 0.4, 1.62), 0.025, mat("#f2f2f2"), uclar=False)
tabela(B + 1.5, 0.3, 1.38, "DONDURMA", "#e94f4f", "#ffffff", gen=1.2, yuk=0.28)
for k, c in enumerate(("#ffd54a", "#ff9ad0", "#8fd16a")):
    koni("kulah", (B + 1.15 + k * 0.35, 0.5, 1.07), 0.0, 0.06, 0.16, mat("#d9a441", 0.6)); kure("top", (B + 1.15 + k * 0.35, 0.5, 1.2), (0.07, 0.07, 0.07), mat(c, 0.35, sss=0.1))
for k in range(4):   # pamuk şeker çubukları
    xx = B + 0.95 + k * 0.33; silindir("cubuk", (xx, 0.85, 1.0), (xx, 0.85, 1.35), 0.01, mat("#ffffff"), uclar=False)
    kure("pamuk_seker", (xx, 0.85, 1.45), (0.13, 0.13, 0.15), mat("#ffa8d8", 0.95, sss=0.3))
# martılar (biri zıplar)
def marti(x, y, s=1.0):
    g = grup("marti", (x, y, 0)); m = mat("#f4f4f4", 0.6)
    kure("marti_govde", (x, y, 0.18 * s), (0.2 * s, 0.12 * s, 0.12 * s), m, parent=g); kure("marti_kafa", (x - 0.2 * s, y, 0.3 * s), (0.08 * s,) * 3, m, parent=g)
    koni("marti_gaga", (x - 0.31 * s, y, 0.3 * s), 0.025 * s, 0.0, 0.1 * s, mat("#f2b632", 0.4), parent=g, rot=(0, -90, 0))
    for sd in (-1, 1): kutu("marti_kanat", (x + 0.03 * s, y + sd * 0.12 * s, 0.22 * s), (0.16 * s, 0.04 * s, 0.02 * s), m, parent=g, rot=(sd * 12, 0, 0))
    for k in range(3): kure("seker_damla", (x - 0.05 * s + k * 0.08 * s, y - 0.1 * s, 0.28 * s), (0.05 * s, 0.05 * s, 0.04 * s), mat("#ff8fc8", 0.25, sss=0.1), parent=g)
    return g
m1 = marti(B - 2.4, -0.2, 1.3); m2 = marti(B - 3.1, 0.4, 1.3)
for k in range(b(9), SON, 12): anahtar(m1, k, loc=(B - 2.4, -0.2, 0)); anahtar(m1, k + 6, loc=(B - 2.4, -0.2, 0.22))
for k in range(b(9) + 3, SON, 8): anahtar(m2, k, rot=(0, 0, 0)); anahtar(m2, k + 4, rot=(0, 10, 0))
gorunur(m1, [(1, True)]);
# şeker yağmuru
yag = bos("yagmur", (B, 0, 0))
for k in range(150):
    d = kure("seker_damla", (B + R(-5, 5), R(-2.2, 2.0), R(0.3, 14)), (0.075, 0.075, 0.13), mat("#ff8fc8", 0.25, sss=0.1), parent=yag, seg=12)
    gorunur(d, [(1, False), (b(7) + 8, True), (b(11), False)])
anahtar(yag, b(7) + 8, loc=(B, 0, 0)); anahtar(yag, b(11), loc=(B, 0, -12)); lineer(yag)
# yapışkan birikintiler + şemsiyelerde pembe akıntı
for (px, py, r) in [(-1.2, -0.3, 0.35), (0.9, -0.6, 0.3), (-0.2, 0.6, 0.4), (2.4, -0.2, 0.3), (-3.0, -1.0, 0.45), (3.4, -1.2, 0.4)]:
    p_ = kure("seker_birikinti", (B + px, py, 0.0), (r, r * 0.8, 0.04), mat("#ff8fc8", 0.2, sss=0.1)); gorunur(p_, [(1, False), (b(9), True)])
for sx, sy in ((B + 2.9, 0.9), (B - 2.6, 1.1)):
    for k in range(5):
        a = math.radians(k * 72); d = kure("akinti", (sx + math.cos(a) * 0.75, sy + math.sin(a) * 0.4, 1.72), (0.08, 0.08, 0.16), mat("#ff8fc8", 0.25, sss=0.1))
        gorunur(d, [(1, False), (b(8), True)])

# ---------- MEKÂN C: bilgi stüdyosu (terazi) ----------
mekan_ic(C, "mavi", "ahsap", isik_guc=0.95)
for k in range(6): kutu("raf_kutu", (C - 3.2 + k * 0.25, 1.0, 1.6 + (k % 2) * 0.05), (0.1, 0.1, 0.12 + (k % 3) * 0.03), mat(("#ffd54a", "#e94f4f", "#8fd16a")[k % 3], 0.6))
kutu("raf", (C - 2.6, 1.0, 1.45), (0.9, 0.18, 0.03), mat("#a8703f"))
kutu("tablo", (C - 2.4, 1.18, 2.6), (0.6, 0.02, 0.45), mat("#fff3c4", 0.7)); 
for k in range(3): kure("tablo_bulut", (C - 2.6 + k * 0.2, 1.15, 2.6 + (k % 2) * 0.06), (0.16, 0.03, 0.12), mat("#ffffff", 0.8))
# terazi: solda bulut, sağda 500 TON ağırlık
kutu("terazi_ayak", (C + 1.4, 0.5, 0.45), (0.08, 0.08, 0.45), mat("#c9a227", 0.3, metal=0.6))
ter = bos("terazi_kol", (C + 1.4, 0.5, 0.95))
kutu("terazi_cubuk", (C + 1.4, 0.5, 0.95), (0.9, 0.04, 0.03), mat("#c9a227", 0.3, metal=0.6), parent=ter)
for dx in (-0.85, 0.85): silindir("kefe", (C + 1.4 + dx, 0.5, 0.78), (C + 1.4 + dx, 0.5, 0.8), 0.28, mat("#c9a227", 0.3, metal=0.6), parent=ter, uclar=False)
for dx, r in [(-0.12, 0.2), (0.08, 0.26), (0.25, 0.18)]: kure("bulut", (C + 0.55 + dx, 0.5, 1.0 + (0.05 if r > 0.2 else 0)), (r, r * 0.8, r * 0.7), mat("#ffffff", 0.9, sss=0.2), parent=ter)
kutu("agirlik", (C + 2.25, 0.5, 1.0), (0.22, 0.2, 0.2), mat("#3d3d46", 0.5), parent=ter)
yazi("500\nTON", (C + 2.25, 0.28, 1.0), boy=0.11, renk="#ffffff", parent=ter)
anahtar(ter, b(13), rot=(0, 8, 0)); anahtar(ter, b(13) + 10, rot=(0, -6, 0)); anahtar(ter, b(13) + 18, rot=(0, 3, 0)); anahtar(ter, b(13) + 26, rot=(0, 0, 0))
for k in range(6):
    d = kure("damla", (C + 0.4 + k * 0.12, 0.5, 0.6), (0.04, 0.04, 0.07), mat("#5fb8f0", 0.15, sss=0.1)); k0 = b(13) + k * 7
    anahtar(d, k0, loc=(C + 0.4 + k * 0.08, 0.5, 0.75)); anahtar(d, k0 + 14, loc=(C + 0.4 + k * 0.08, 0.5, 0.0)); lineer(d)

# ---------- KARAKTERLER ----------
t = karakter("tahsin", x=A - 0.2)
cocuk = karakter("cocuk", x=B - 1.3, y=-0.1, sac="kivircik", sac_renk="#3b2a1a", gomlek="#ffd54a", sort="#3d6fb5", kravat="#ffd54a", gozluk=False, boy=0.78)
hasan = karakter("hasan", x=B + 1.5, y=0.0, sac="sapka", sac_renk="#ffffff", gomlek="#ffffff", sort="#e94f4f", kravat="#e94f4f", gozluk=False, boy=1.0)

# ---------- OYUN ----------
t.ifade(1, "sasirmis"); t.poz(1, "sasir", gecis=0); t.zipla(8, 0.3)
t.ifade(b(1), "gulumse"); t.poz(b(1), "anlat"); t.poz(b(1) + 30, "isaret_sag")
t.poz(b(2), "sevin"); t.ifade(b(2), "mutlu"); t.zipla(b(2) + 8, 0.25)
t.yuru(b(3) - 16, b(3) + 2, A + 0.55); t.poz(b(3) + 6, "tut"); t.ifade(b(3), "dusunceli")
t.poz(b(4) + 14, "sasir"); t.ifade(b(4) + 14, "sasirmis"); t.bak(b(4) + 18, -10); t.zipla(b(4) + 40, 0.35); t.poz(b(4) + 40, "sevin"); t.ifade(b(4) + 40, "mutlu")
t.isinlan(b(5), B - 0.2, -0.3); t.poz(b(5), "sevin"); t.ifade(b(5), "mutlu"); t.bak(b(5), 0)
cocuk.ifade(1, "mutlu"); cocuk.poz(1, "sevin", gecis=0); hasan.ifade(1, "gulumse"); hasan.poz(1, "tut", gecis=0)
for k in (b(5) + 2, b(5) + 22, b(5) + 42): cocuk.zipla(k, 0.45)
t.zipla(b(5) + 12, 0.3)
hasan.ifade(b(6), "mutlu"); hasan.poz(b(6), "sevin"); hasan.zipla(b(6) + 4, 0.3); hasan.yuru(b(6) + 14, e(6), B + 0.7, -0.2)
cocuk.poz(b(6) + 10, "el_salla")
t.poz(b(7), "dusun"); t.ifade(b(7), "dusunceli"); t.bak(b(7) + 6, 0)
for c in (cocuk, hasan): c.poz(b(7) + 4, "isaret_ileri"); c.ifade(b(7) + 4, "sasirmis")
t.poz(b(8), "korku"); t.ifade(b(8), "korkmus"); t.zipla(b(8) + 2, 0.2)
for c in (cocuk, hasan): c.poz(b(8) + 3, "korku"); c.ifade(b(8) + 3, "korkmus")
for c in (t, cocuk, hasan): c.poz(b(9), "uzgun"); c.ifade(b(9), "sikkin")
for k in range(b(9) + 4, e(10), 10):   # yapışıp kalan ayak: küçük çırpınma
    for c in (t, cocuk, hasan): c.bak(k, 8 if (k // 10) % 2 else -8, gecis=4)
hasan.poz(b(10), "isaret_sol"); hasan.ifade(b(10), "uzgun")
t.isinlan(b(11), A + 0.55, 0); t.poz(b(11), "tut"); t.ifade(b(11), "kizgin")
t.poz(b(12) + 6, "sevin"); t.ifade(b(12) + 6, "mutlu"); t.zipla(b(12) + 8, 0.3)
t.isinlan(b(13), C - 0.7, 0); t.poz(b(13), "isaret_sag"); t.ifade(b(13), "gulumse")
t.poz(b(14), "sasir"); t.ifade(b(14), "sasirmis")
t.poz(b(15), "anlat"); t.ifade(b(15), "gulumse")
t.poz(b(16), "omuz_silk"); t.ifade(b(16), "dusunceli")
t.nefes(1, SON); cocuk.nefes(1, SON); hasan.nefes(1, SON)
t.konus(SES, 0, SURE)

# ---------- KAMERA (çoğu geniş, sürekli hafif itme) ----------
def cek(k0, k1, cekim, hedef, aci=0, z=None, oran=0.9):
    kamera_cek(k0, cekim, hedef, aci=aci, z_hedef=z); kamera_it(k0, k1, oran)
cek(1, b(1), "genis", (A + 0.4, 0), aci=-6, z=1.8, oran=0.88)
cek(b(1), b(2), "cok_genis", (A, 0.2), aci=-14, z=1.9)
cek(b(2), b(3), "orta", (A + 0.6, 0), aci=16, z=1.6)
cek(b(3), b(4) - 2, "yakin", (A + 1.1, 0), aci=30, z=1.3)
cek(b(4) - 2, b(5), "cok_genis", (A + 0.5, 0), aci=8, z=2.6, oran=0.85)
cek(b(5), b(6), "genis", (B - 0.3, 0), aci=-8)
cek(b(6), b(7), "orta", (B + 1.1, 0), aci=-14)
cek(b(7), b(8), "cok_genis", (B, 0), aci=10, z=2.2)
cek(b(8), b(9), "genis", (B - 0.3, 0), aci=-10, z=2.6, oran=0.85)
cek(b(9), b(10), "genis", (B - 0.2, 0), aci=-12)
cek(b(10), b(11), "orta", (B - 2.7, 0.1), aci=-10, z=0.6)
cek(b(11), b(12), "orta", (A + 0.85, 0), aci=-18, z=1.6)
cek(b(12), b(13), "cok_genis", (A + 0.4, 0), aci=6, z=2.4, oran=1.08)
cek(b(13), b(15), "genis", (C + 0.4, 0), aci=-6, z=1.5)
cek(b(15), b(16), "orta", (C + 0.4, 0), aci=14, z=1.5)
cek(b(16), SON, "genis", (C, 0), aci=4, z=1.6, oran=0.88)

if "--kare" in sys.argv:
    for k in sys.argv[sys.argv.index("--kare") + 1].split(","): kare_al(os.path.join(W, f"kare_{int(k):04d}.png"), int(k))
if "--kontak" in sys.argv:
    ks = [b(i) + 10 for i in range(len(PH))]
    for k in ks: kare_al(os.path.join(W, "kontak", f"k_{k:04d}.png"), k)
if "--render" in sys.argv:
    if "--aralik" in sys.argv:
        a0, a1 = map(int, sys.argv[sys.argv.index("--aralik") + 1].split("-")); render_et(os.path.join(W, "kareler2"), a0, a1)
    else: render_et(os.path.join(W, "kareler2"))
