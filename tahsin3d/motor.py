"""Tuhaf Tahsin 3D motoru (Blender bpy + Cycles, GPU'suz bulutta çalışır).

Bir bölüm betiği bu modülü içe aktarır, sahneyi kurar, karakterleri oynatır ve render eder:

    import sys; sys.path.insert(0, "<repo>/tahsin3d"); from motor import *
    yeni_sahne(sure_sn=36.5)
    oda = mekan_oda(x=0, duvar="tugla")                  # mekân parçaları
    t = karakter("tahsin", x=0)                          # Tahsin (referans: referans/tahsin-3d-referans.png)
    t.poz(sn(0.0), "dur"); t.poz(sn(1.2), "el_salla")    # poz kütüphanesi: POZLAR
    t.ifade(sn(0.0), "gulumse")                          # ifade kütüphanesi: IFADELER
    t.konus("work/voice.wav", 0, 36.5)                   # sese göre ağız (dudak senkronu)
    kamera_cek(sn(0), "genis", hedef=t)                  # çekim: genis/orta/yakin/asiri_yakin + kesme
    render_et("work/kareler")                            # Cycles, 432x768, 24 fps

Bütün zamanlar KARE numarasıdır (1'den başlar). sn(t) saniyeyi kareye çevirir.
Ayarlar ortamdan: RES (genişlik, varsayılan 432), SAMPLES (8), BOUNCES (2), FPS (24).
"""
import bpy
import bmesh, math, os, random, subprocess, wave
import numpy as np
from mathutils import Vector

FPS = int(os.environ.get("FPS", "24"))
RES = int(os.environ.get("RES", "432"))
SAMPLES = int(os.environ.get("SAMPLES", "8"))
BOUNCES = int(os.environ.get("BOUNCES", "2"))
BURASI = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(BURASI, "font", "ArchivoBlack-Regular.ttf")
S = None


def sn(t):
    """Saniye -> kare numarası."""
    return int(round(t * FPS)) + 1


# ------------------------------------------------------------------ temel
def srgb(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


_MATS = {}


def mat(renk, rough=0.55, sss=0.0, metal=0.0, emit=0.0, ad=None):
    """Kil görünümlü malzeme. renk: '#rrggbb'. Aynı parametreler tekrar kullanılır."""
    key = (renk, rough, sss, metal, emit)
    if key in _MATS: return _MATS[key]
    m = bpy.data.materials.new(ad or f"m_{renk}"); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; rgb = srgb(renk)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.3, 0.15, 0.1); b.inputs["Subsurface Scale"].default_value = 0.05
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1); b.inputs["Emission Strength"].default_value = emit
    _MATS[key] = m
    return m


def _upd(): bpy.context.view_layer.update()


def _set(o, m=None, parent=None, smooth=True, subsurf=0):
    if m is not None and o.type in ("MESH", "FONT", "CURVE"):
        o.data.materials.clear(); o.data.materials.append(m)
    if smooth and o.type == "MESH":
        for p in o.data.polygons: p.use_smooth = True
    if subsurf:
        md = o.modifiers.new("ss", "SUBSURF"); md.levels = subsurf; md.render_levels = subsurf
    if parent is not None:
        _upd(); mw = o.matrix_world.copy(); o.parent = parent; o.matrix_world = mw
    return o


def kure(ad, loc, olcek, m, parent=None, seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=1, location=loc)
    o = bpy.context.object; o.name = ad; o.scale = olcek
    return _set(o, m, parent)


def kutu(ad, loc, olcek, m, parent=None, bevel=0.03, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc, rotation=[math.radians(r) for r in rot])
    o = bpy.context.object; o.name = ad; o.scale = olcek
    if bevel:
        bpy.ops.object.transform_apply(scale=True)
        b = o.modifiers.new("bevel", "BEVEL"); b.width = bevel; b.segments = 3
    return _set(o, m, parent)


def silindir(ad, a, b, r, m, parent=None, uclar=True, seg=20):
    a, b = Vector(a), Vector(b); d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=max(d.length, 1e-4), location=(a + b) / 2)
    o = bpy.context.object; o.name = ad
    o.rotation_mode = "QUATERNION"; o.rotation_quaternion = d.to_track_quat("Z", "Y")
    _set(o, m, parent)
    caps = []
    if uclar:
        caps = [kure(ad + "_ucA", a, (r, r, r), m, parent, 12), kure(ad + "_ucB", b, (r, r, r), m, parent, 12)]
    o["uclar"] = [c.name for c in caps]
    return o


def koni(ad, loc, r1, r2, h, m, parent=None, rot=(0, 0, 0), seg=24):
    bpy.ops.mesh.primitive_cone_add(vertices=seg, radius1=r1, radius2=r2, depth=h, location=loc, rotation=[math.radians(r) for r in rot])
    return _set(bpy.context.object, m, parent)


def halka(ad, loc, R, r, m, parent=None, rot=(90, 0, 0), yarim=None):
    """Torus. yarim='ust' / 'alt': yarısını sil (gülüş, mutlu göz yayı)."""
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=[math.radians(x) for x in rot],
                                     major_segments=32, minor_segments=10)
    o = bpy.context.object; o.name = ad
    if yarim:
        bm = bmesh.new(); bm.from_mesh(o.data)
        sil = [v for v in bm.verts if (v.co.y < 0.005 if yarim == "ust" else v.co.y > -0.005)]
        bmesh.ops.delete(bm, geom=sil, context="VERTS"); bm.to_mesh(o.data); bm.free()
    return _set(o, m, parent)


def bos(ad, loc, parent=None):
    o = bpy.data.objects.new(ad, None); S.collection.objects.link(o); o.location = loc; o.empty_display_size = 0.1
    if parent is not None:
        _upd(); o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o


def yazi(metin, loc, boy=0.3, renk="#ffffff", derinlik=0.05, rot=(90, 0, 0), parent=None, ortala=True, emit=0.0):
    """3D yazı (Türkçe karakterli font). rot=(90,0,0): kameraya dönük dik yazı."""
    bpy.ops.object.text_add(location=loc, rotation=[math.radians(r) for r in rot])
    o = bpy.context.object; o.data.body = metin; o.data.size = boy; o.data.extrude = derinlik
    o.data.bevel_depth = derinlik * 0.3; o.data.bevel_resolution = 2
    if os.path.exists(FONT): o.data.font = bpy.data.fonts.load(FONT, check_existing=True)
    if ortala: o.data.align_x = "CENTER"; o.data.align_y = "CENTER"
    return _set(o, mat(renk, 0.4, emit=emit), parent, smooth=False)


def gorunur(o, kareler):
    """kareler: [(kare, True/False), ...] — o kareden itibaren görünür/görünmez."""
    objs = [o] + [bpy.data.objects[n] for n in o.get("uclar", []) if n in bpy.data.objects] if isinstance(o, bpy.types.Object) else list(o)
    for x in objs:
        for f, v in kareler:
            x.hide_render = not v; x.hide_viewport = not v
            x.keyframe_insert("hide_render", frame=f); x.keyframe_insert("hide_viewport", frame=f)


def anahtar(o, kare, loc=None, rot=None, olcek=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=kare)
    if rot is not None: o.rotation_euler = [math.radians(r) for r in rot]; o.keyframe_insert("rotation_euler", frame=kare)
    if olcek is not None:
        o.scale = (olcek, olcek, olcek) if isinstance(olcek, (int, float)) else olcek; o.keyframe_insert("scale", frame=kare)


def zipla_belir(o, kare, sure=8, son=1.0):
    """Nesneyi 0'dan son ölçeğe zıplatarak getirir (pop-in)."""
    anahtar(o, kare - 1, olcek=0.001); anahtar(o, kare + sure * 2 // 3, olcek=son * 1.15); anahtar(o, kare + sure, olcek=son)


# ------------------------------------------------------------------ sahne
def yeni_sahne(sure_sn, arka="#3a2418"):
    global S
    bpy.ops.wm.read_factory_settings(use_empty=True); _MATS.clear()
    S = bpy.context.scene; S.render.fps = FPS; S.frame_start = 1; S.frame_end = sn(sure_sn) - 1
    w = bpy.data.worlds.new("dunya"); S.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (*srgb(arka), 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.3
    S.render.engine = "CYCLES"; S.cycles.device = "CPU"; S.cycles.samples = SAMPLES
    S.cycles.use_denoising = True; S.cycles.denoiser = "OPENIMAGEDENOISE"
    S.cycles.max_bounces = BOUNCES; S.cycles.diffuse_bounces = min(2, BOUNCES); S.cycles.glossy_bounces = min(2, BOUNCES)
    S.cycles.transmission_bounces = 0; S.cycles.transparent_max_bounces = 4
    S.render.resolution_x = RES; S.render.resolution_y = RES * 16 // 9; S.render.resolution_percentage = 100
    S.view_settings.view_transform = "AgX"; S.view_settings.look = "AgX - Punchy"; S.view_settings.exposure = -0.3
    S.render.use_persistent_data = True
    bpy.ops.object.camera_add(location=(0, -5, 1.6)); cam = bpy.context.object; cam.name = "kamera"; S.camera = cam
    cam.data.lens = 40; cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 4.5; cam.rotation_mode = "XYZ"
    return S


def isik(ad, tur, loc, guc, renk="#ffe0c0", boyut=1.5, hedef=(0, 0, 1.4), aci=70):
    bpy.ops.object.light_add(type=tur, location=loc); L = bpy.context.object; L.name = ad
    L.data.energy = guc; L.data.color = srgb(renk)
    if tur == "AREA": L.data.size = boyut
    if tur == "SPOT": L.data.spot_size = math.radians(aci); L.data.spot_blend = 0.4
    L.rotation_euler = (Vector(hedef) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return L


def isik_seti(x=0, ana="#ffd9b0", kontur="#ffb070", guc=1.0):
    """Mekân başına standart sıcak stüdyo ışığı (referanstaki gibi)."""
    isik(f"ana_{x}", "AREA", (x - 2.2, -3.0, 3.6), 420 * guc, ana, 2.5, (x, 0, 1.4))
    isik(f"dolgu_{x}", "AREA", (x + 2.8, -2.5, 2.0), 110 * guc, "#e8eeff", 3, (x, 0, 1.4))
    isik(f"kontur_{x}", "AREA", (x + 1.5, 1.0, 3.8), 350 * guc, kontur, 1.5, (x, 0, 1.6))
    isik(f"tepe_{x}", "SPOT", (x, -1.2, 4.6), 380 * guc, "#ffad66", hedef=(x, 1.2, 2.0))


# ------------------------------------------------------------------ dokular
def _duvar_mat(tur, renk1, renk2, harc):
    m = bpy.data.materials.new(f"duvar_{tur}_{renk1}"); m.use_nodes = True; nt = m.node_tree
    pb = nt.nodes["Principled BSDF"]; tc = nt.nodes.new("ShaderNodeTexCoord")
    if tur == "tugla":
        bk = nt.nodes.new("ShaderNodeTexBrick"); bk.offset = 0.5
        bk.inputs["Color1"].default_value = (*srgb(renk1), 1); bk.inputs["Color2"].default_value = (*srgb(renk2), 1)
        bk.inputs["Mortar"].default_value = (*srgb(harc), 1); bk.inputs["Scale"].default_value = 3.2; bk.inputs["Mortar Size"].default_value = 0.012
        nt.links.new(tc.outputs["Object"], bk.inputs["Vector"]); nt.links.new(bk.outputs["Color"], pb.inputs["Base Color"])
        bu = nt.nodes.new("ShaderNodeBump"); bu.inputs["Strength"].default_value = 0.4
        nt.links.new(bk.outputs["Fac"], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], pb.inputs["Normal"]); pb.inputs["Roughness"].default_value = 0.8
    elif tur == "ahsap":
        wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.inputs["Scale"].default_value = 1.2
        wv.inputs["Distortion"].default_value = 6; wv.inputs["Detail"].default_value = 3
        mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.4, 3, 1)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
        rp = nt.nodes.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].color = (*srgb(renk1), 1); rp.color_ramp.elements[1].color = (*srgb(renk2), 1)
        nt.links.new(wv.outputs["Fac"], rp.inputs["Fac"]); nt.links.new(rp.outputs["Color"], pb.inputs["Base Color"]); pb.inputs["Roughness"].default_value = 0.35
    elif tur == "karo":
        ck = nt.nodes.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 6
        ck.inputs["Color1"].default_value = (*srgb(renk1), 1); ck.inputs["Color2"].default_value = (*srgb(renk2), 1)
        nt.links.new(tc.outputs["Object"], ck.inputs["Vector"]); nt.links.new(ck.outputs["Color"], pb.inputs["Base Color"]); pb.inputs["Roughness"].default_value = 0.3
    else:  # sıva / düz boya: hafif gürültülü
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 8
        rp = nt.nodes.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].color = (*srgb(renk1), 1); rp.color_ramp.elements[1].color = (*srgb(renk2), 1)
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], rp.inputs["Fac"]); nt.links.new(rp.outputs["Color"], pb.inputs["Base Color"])
        pb.inputs["Roughness"].default_value = 0.85
    return m


DUVARLAR = {"tugla": ("tugla", "#9a4424", "#83381d", "#5a2a17"), "krem": ("siva", "#e8d6b5", "#d9c39c", None),
            "mavi": ("siva", "#6f9fc4", "#5e8db3", None), "yesil": ("siva", "#8fb878", "#7ea767", None),
            "pembe": ("siva", "#e8a5a5", "#d99494", None), "lacivert": ("siva", "#2b3a5c", "#22304d", None),
            "karo": ("karo", "#f2f2f2", "#cfd8dc", None), "ahsap": ("ahsap", "#8a5a2e", "#b07a40", None)}
ZEMINLER = {"ahsap": ("ahsap", "#8a5a2e", "#c08a4c"), "karo": ("karo", "#e9e4da", "#b9b2a4"), "cim": ("siva", "#5c9c3c", "#4c8a30"),
            "asfalt": ("siva", "#4a4a4f", "#3c3c42"), "kum": ("siva", "#e6c88e", "#d6b479"), "hali": ("siva", "#a33b3b", "#8e3030")}


def duvar(x=0, tur="tugla", gen=12, yuk=10, y=1.2):
    t = DUVARLAR[tur]
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, yuk / 2 - 0.8), rotation=(math.radians(90), 0, 0))
    o = bpy.context.object; o.name = f"duvar_{x}"; o.scale = (gen, yuk, 1)
    o.data.materials.append(_duvar_mat(t[0], t[1], t[2], t[3] or t[2])); return o


def zemin(x=0, tur="ahsap", gen=12, der=9):
    t = ZEMINLER[tur]
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, -1.5 + 1.2, 0)); o = bpy.context.object; o.name = f"zemin_{x}"; o.scale = (gen, der, 1)
    o.data.materials.append(_duvar_mat(t[0], t[1], t[2], t[2])); return o


def gokyuzu(x=0, renk1="#8fd0ff", renk2="#d8f0ff", gen=18, yuk=12, y=4):
    """Dış mekân için gökyüzü fonu (hafif ışıklı)."""
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, yuk / 2 - 1), rotation=(math.radians(90), 0, 0))
    o = bpy.context.object; o.name = f"gok_{x}"; o.scale = (gen, yuk, 1)
    m = bpy.data.materials.new(f"gok_{x}"); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
    em = nt.nodes.new("ShaderNodeEmission"); gr = nt.nodes.new("ShaderNodeTexGradient"); tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, 0, math.radians(90)); mp.inputs["Location"].default_value = (0, 0.5, 0)
    rp = nt.nodes.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].color = (*srgb(renk2), 1); rp.color_ramp.elements[1].color = (*srgb(renk1), 1)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], gr.inputs["Vector"])
    nt.links.new(gr.outputs["Fac"], rp.inputs["Fac"]); nt.links.new(rp.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 1.0
    nt.links.new(em.outputs["Emission"], nt.nodes["Material Output"].inputs["Surface"]); o.data.materials.append(m)
    return o


def mekan_ic(x=0, duvar_turu="tugla", zemin_turu="ahsap", isik_guc=1.0):
    """İç mekân: arka duvar + zemin + ışık. Tahsin'in durduğu nokta (x, 0)."""
    duvar(x, duvar_turu); zemin(x, zemin_turu); isik_seti(x, guc=isik_guc)


def mekan_dis(x=0, zemin_turu="cim", gok=("#8fd0ff", "#d8f0ff"), gunes=True):
    """Dış mekân: gökyüzü fonu + zemin + güneş ışığı."""
    gokyuzu(x, *gok); zemin(x, zemin_turu, gen=14, der=10)
    isik(f"gunes_{x}", "SUN", (x - 3, -4, 6), 3.2, "#fff1d6", hedef=(x, 0, 0)).data.angle = math.radians(8)
    isik(f"dolgu_{x}", "AREA", (x + 2.8, -2.5, 2.0), 90, "#e8eeff", 3, (x, 0, 1.4))
    if gunes:
        kure(f"gunes_top_{x}", (x + 2.6, 4, 5.2), (0.6, 0.6, 0.6), mat("#ffd54a", emit=4.0))


# ------------------------------------------------------------------ eşyalar (hepsi basit, kil görünümlü)
def masa(x, y=0.6, renk="#a8703f", gen=1.4):
    kutu("masa_ust", (x, y, 0.75), (gen / 2, 0.4, 0.04), mat(renk, 0.5))
    for dx in (-1, 1):
        for dy in (-1, 1):
            silindir("masa_ayak", (x + dx * (gen / 2 - 0.08), y + dy * 0.32, 0), (x + dx * (gen / 2 - 0.08), y + dy * 0.32, 0.72), 0.035, mat(renk, 0.5), uclar=False)


def sandalye(x, y=0.4, renk="#c0392b"):
    m = mat(renk, 0.5); kutu("sandalye_oturak", (x, y, 0.45), (0.22, 0.22, 0.03), m); kutu("sandalye_sirt", (x, y + 0.2, 0.75), (0.22, 0.03, 0.28), m)
    for dx in (-1, 1):
        for dy in (-1, 1):
            silindir("sandalye_ayak", (x + dx * 0.18, y + dy * 0.18, 0), (x + dx * 0.18, y + dy * 0.18, 0.43), 0.025, m, uclar=False)


def bardak(x, y, z, renk="#c0392b", cay=True):
    """İnce belli çay bardağı + tabak."""
    cam = bpy.data.materials.new("cam"); cam.use_nodes = True; b = cam.node_tree.nodes["Principled BSDF"]
    b.inputs["Transmission Weight"].default_value = 0.9; b.inputs["Roughness"].default_value = 0.05; b.inputs["Base Color"].default_value = (1, 1, 1, 1)
    koni("bardak_alt", (x, y, z + 0.06), 0.045, 0.035, 0.12, cam); koni("bardak_ust", (x, y, z + 0.16), 0.035, 0.05, 0.08, cam)
    if cay: koni("cay", (x, y, z + 0.08), 0.042, 0.036, 0.13, mat("#9b2c0e", 0.2, sss=0.3))
    silindir("tabak", (x, y, z), (x, y, z + 0.012), 0.09, mat(renk, 0.3), uclar=False)


def kutu_esya(x, y, z, boyut=0.3, renk="#d9a441", ad="kutu"):
    return kutu(ad, (x, y, z + boyut / 2), (boyut / 2, boyut / 2, boyut / 2), mat(renk, 0.6))


def top(x, y, z, r=0.15, renk="#e74c3c", ad="top"):
    return kure(ad, (x, y, z + r), (r, r, r), mat(renk, 0.4, sss=0.05))


def agac(x, y=1.0, boy=2.2, yaprak="#4caf50", govde="#7a4b2a"):
    silindir("agac_govde", (x, y, 0), (x, y, boy * 0.55), 0.1, mat(govde, 0.7), uclar=False)
    for i, (dx, dz, r) in enumerate([(0, 0.75, 0.55), (-0.3, 0.6, 0.4), (0.32, 0.62, 0.42), (0, 0.95, 0.4)]):
        kure("agac_yaprak", (x + dx, y, boy * dz), (r, r * 0.9, r * 0.85), mat(yaprak, 0.6, sss=0.05))


def bulut(x, y, z, olcek=1.0):
    m = mat("#ffffff", 0.9, sss=0.2)
    for dx, r in [(-0.35, 0.3), (0, 0.42), (0.38, 0.32), (0.15, 0.3)]:
        kure("bulut", (x + dx * olcek, y, z + (0.1 if r > 0.4 else 0) * olcek), (r * olcek, r * olcek * 0.8, r * olcek * 0.7), m)


def bina(x, y=3, gen=1.6, yuk=3.5, renk="#e0b07a", pencere="#ffe9a8"):
    kutu("bina", (x, y, yuk / 2), (gen / 2, 0.6, yuk / 2), mat(renk, 0.8), bevel=0.04)
    for i in range(int(yuk / 0.8)):
        for j in (-1, 1):
            kutu("pencere", (x + j * gen * 0.22, y - 0.61, 0.6 + i * 0.8), (0.16, 0.01, 0.2), mat(pencere, 0.3, emit=0.6), bevel=0)


def tabela(x, y, z, metin, zemin_renk="#2e7d32", yazi_renk="#ffffff", gen=1.6, yuk=0.45):
    kutu("tabela", (x, y, z), (gen / 2, 0.04, yuk / 2), mat(zemin_renk, 0.5))
    yazi(metin, (x, y - 0.05, z), boy=yuk * 0.5, renk=yazi_renk, derinlik=0.01)


# ------------------------------------------------------------------ karakter
POZLAR = {
    # kol açıları: (X, Y, Z) derece. S=sağ kol (Tahsin'in solu, ekranda sağda), L=sol kol (ekranda solda)
    "dur": dict(S=(0, -8, 0), L=(0, 8, 0), kafa=(0, 0, 0), govde=(0, 0, 0)),
    "el_salla": dict(S=(0, -150, 0), L=(0, 8, 0), kafa=(0, 6, 0), govde=(0, 0, 0)),
    "dusun": dict(S=(-130, 0, -35), L=(0, 10, 0), kafa=(6, -10, 4), govde=(0, 0, 0)),
    "sasir": dict(S=(-15, -135, 0), L=(-15, 135, 0), kafa=(-8, 0, 0), govde=(0, 0, 0)),
    "fikir": dict(S=(0, -10, 0), L=(0, 95, 0), kafa=(-4, 10, -4), govde=(0, 0, 0)),
    "isaret_sag": dict(S=(0, -95, 0), L=(0, 10, 0), kafa=(0, 0, -12), govde=(0, 0, -8)),
    "isaret_sol": dict(S=(0, -10, 0), L=(0, 95, 0), kafa=(0, 0, 12), govde=(0, 0, 8)),
    "isaret_ileri": dict(S=(-90, 0, 0), L=(0, 10, 0), kafa=(0, 0, 0), govde=(0, 0, 0)),
    "omuz_silk": dict(S=(0, -55, 30), L=(0, 55, -30), kafa=(0, 10, 0), govde=(0, 0, 0)),
    "sevin": dict(S=(0, -165, 0), L=(0, 165, 0), kafa=(-10, 0, 0), govde=(0, 0, 0)),
    "uzgun": dict(S=(10, -4, 0), L=(10, 4, 0), kafa=(18, 0, 0), govde=(8, 0, 0)),
    "kizgin": dict(S=(0, -35, -40), L=(0, 35, 40), kafa=(8, 0, 0), govde=(4, 0, 0)),   # eller belde
    "anlat": dict(S=(-40, -45, 0), L=(-40, 45, 0), kafa=(0, 0, 0), govde=(0, 0, 0)),
    "tut": dict(S=(-80, -20, 0), L=(-80, 20, 0), kafa=(10, 0, 0), govde=(0, 0, 0)),     # önünde bir şey tutar
    "korku": dict(S=(-120, -30, -20), L=(-120, 30, 20), kafa=(-6, 0, 0), govde=(-6, 0, 0)),
    "selam": dict(S=(-150, -20, -60), L=(0, 8, 0), kafa=(0, 0, 0), govde=(0, 0, 0)),
}
IFADELER = {
    # agiz: gulus | duz | acik | uzgun | genis_gulus;  goz: normal | mutlu | buyuk | yarim;  kas: normal | kalkik | kizgin | uzgun | tek
    "gulumse": dict(agiz="gulus", goz="normal", kas="normal"),
    "duz": dict(agiz="duz", goz="normal", kas="normal"),
    "dusunceli": dict(agiz="duz", goz="normal", kas="tek"),
    "sasirmis": dict(agiz="acik", goz="buyuk", kas="kalkik"),
    "mutlu": dict(agiz="genis_gulus", goz="mutlu", kas="kalkik"),
    "uzgun": dict(agiz="uzgun", goz="normal", kas="uzgun"),
    "kizgin": dict(agiz="duz", goz="normal", kas="kizgin"),
    "korkmus": dict(agiz="acik", goz="buyuk", kas="uzgun"),
    "sikkin": dict(agiz="uzgun", goz="yarim", kas="normal"),
}
SACLAR = ("tahsin", "kel", "topuz", "kep", "kivircik", "at_kuyrugu", "sapka")


class Karakter:
    def __init__(self, ad, x=0, y=0, sac="tahsin", ten="#e6cfb1", gomlek="#ece0c8", sort="#1f7a40", kravat="#1f7a40",
                 sac_renk="#e0711c", bacak="#3c3a2c", gozluk=True, boy=1.0, yuz="#e6cfb1"):
        self.ad = ad; self._ifade = None; self._agiz_durum = {}
        SK, YZ = mat(ten, 0.6, sss=0.15), mat(yuz, 0.6, sss=0.15)
        SH, GR, HR = mat(gomlek, 0.65, sss=0.08), mat(sort, 0.55), mat(sac_renk, 0.5, sss=0.1)
        DK, LG, RIM = mat("#2a211c", 0.35), mat(bacak, 0.6), mat("#2b2b2b", 0.3, metal=0.3)
        WH, MO, TO = mat("#ffffff", 0.2, emit=1.0), mat("#3a1010", 0.5), mat("#d45a5a", 0.5)
        self.kok = bos(f"{ad}_kok", (x, y, 0))
        R = self.kok; X = x; Y = y
        self.govde = bos(f"{ad}_govde", (X, Y, 0.95), R)
        self.kafa = bos(f"{ad}_kafa", (X, Y, 1.62), self.govde)
        self.bacak = {}
        for s in (-1, 1):
            h = bos(f"{ad}_kalca{s}", (X + 0.13 * s, Y, 0.95), self.govde)
            silindir(f"{ad}_bacak{s}", (X + 0.13 * s, Y, 0.95), (X + 0.13 * s, Y, 0.08), 0.045, LG, h)
            kure(f"{ad}_ayak{s}", (X + 0.13 * s, Y - 0.05, 0.05), (0.09, 0.15, 0.05), DK, h); self.bacak[s] = h
        kure(f"{ad}_govde_m", (X, Y, 1.22), (0.33, 0.27, 0.42), SH, self.govde)
        kure(f"{ad}_sort", (X, Y, 1.0), (0.335, 0.275, 0.2), GR, self.govde)
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.09, depth=0.5, location=(X, Y - 0.255, 1.32))
        c = bpy.context.object; c.name = f"{ad}_kravat"; c.rotation_euler = (math.radians(172), 0, math.radians(45)); c.scale = (1, 0.25, 1)
        _set(c, mat(kravat, 0.55), self.govde, smooth=False)
        self.kol = {}
        for s in (-1, 1):
            sh = bos(f"{ad}_omuz{s}", (X + 0.3 * s, Y, 1.45), self.govde)
            silindir(f"{ad}_kol{s}", (X + 0.3 * s, Y, 1.45), (X + 0.36 * s, Y, 1.0), 0.05, SK, sh)
            kure(f"{ad}_el{s}", (X + 0.365 * s, Y, 0.97), (0.07, 0.07, 0.07), SK, sh); self.kol[s] = sh
        H = self.kafa
        kure(f"{ad}_kafa_m", (X, Y, 2.06), (0.6, 0.52, 0.56), YZ, H); kure(f"{ad}_boyun", (X, Y, 1.6), (0.12, 0.12, 0.1), SK, H)
        self._sac(sac, HR, X, Y)
        EY, EZ, EX = Y - 0.49, 2.07, 0.19; self.yuz = {}
        for s in (-1, 1):
            if gozluk: halka(f"{ad}_gozluk{s}", (X + EX * s, EY - 0.03, EZ), 0.125, 0.016, RIM, H)
            e = kure(f"{ad}_goz{s}", (X + EX * s, EY, EZ), (0.052, 0.03, 0.058), DK, H)
            hl = kure(f"{ad}_parlama{s}", (X + EX * s + 0.018, EY - 0.03, EZ + 0.022), (0.013, 0.006, 0.013), WH, H, 10)
            mg = halka(f"{ad}_mutlu_goz{s}", (X + EX * s, EY, EZ - 0.015), 0.05, 0.011, DK, H, yarim="ust")
            yg = kutu(f"{ad}_yarim_kapak{s}", (X + EX * s, EY - 0.005, EZ + 0.03), (0.058, 0.02, 0.03), YZ, H, bevel=0)
            kp = bos(f"{ad}_kas{s}", (X + EX * s, EY + 0.005, EZ + 0.155), H)
            silindir(f"{ad}_kas_m{s}", (X + EX * s - 0.065, EY + 0.005, EZ + 0.155), (X + EX * s + 0.065, EY + 0.005, EZ + 0.155), 0.016, DK, kp)
            self.yuz[s] = dict(goz=e, parlama=hl, mutlu=mg, yarim=yg, kas=kp, kas_z=kp.location.z)
        if gozluk: silindir(f"{ad}_kopru", (X - 0.06, EY - 0.035, EZ + 0.01), (X + 0.06, EY - 0.035, EZ + 0.01), 0.011, RIM, H, uclar=False)
        AZ = 1.86
        self.agiz = dict(
            gulus=halka(f"{ad}_gulus", (X, Y - 0.5, AZ), 0.08, 0.014, DK, H, yarim="alt"),
            genis_gulus=halka(f"{ad}_genis", (X, Y - 0.5, AZ + 0.01), 0.12, 0.018, DK, H, yarim="alt"),
            uzgun=halka(f"{ad}_uzgun", (X, Y - 0.505, AZ - 0.07), 0.07, 0.014, DK, H, yarim="ust"),
            duz=silindir(f"{ad}_duz", (X - 0.05, Y - 0.515, AZ + 0.01), (X + 0.05, Y - 0.515, AZ - 0.01), 0.013, DK, H),
        )
        self.agiz_acik = bos(f"{ad}_agiz_acik", (X, Y - 0.47, 1.8), H)
        kure(f"{ad}_agiz_ic", (X, Y - 0.47, 1.8), (0.1, 0.05, 0.12), MO, self.agiz_acik)
        kure(f"{ad}_dil", (X, Y - 0.505, 1.73), (0.06, 0.02, 0.035), TO, self.agiz_acik, 12)
        self._goz_olcek = {s: tuple(self.yuz[s]["goz"].scale) for s in (-1, 1)}
        self.kok.scale = (boy, boy, boy)
        self.gizli_baslat()

    def _sac(self, tur, HR, X, Y):
        H, ad = self.kafa, self.ad
        if tur == "tahsin":
            bm = bmesh.new(); N = 14; R0, R1, ZB, ZT = 0.6, 0.5, 2.37, 2.97; rb, rt = [], []
            for i in range(N):
                a = 2 * math.pi * i / N; rb.append(bm.verts.new((math.cos(a) * R0, math.sin(a) * R0 * 0.92, ZB)))
            for i in range(N):
                a = 2 * math.pi * i / N; z = ZT if i % 2 == 0 else ZT - 0.3; r = R1 if i % 2 == 0 else R1 * 0.97
                rt.append(bm.verts.new((math.cos(a) * r, math.sin(a) * r * 0.92, z)))
            for i in range(N):
                j = (i + 1) % N; bm.faces.new((rb[i], rb[j], rt[j], rt[i]))
            top_ = bm.verts.new((0, 0, ZT - 0.3)); [bm.faces.new((rt[i], rt[(i + 1) % N], top_)) for i in range(N)]
            bm.faces.new(list(reversed(rb))); me = bpy.data.meshes.new(f"{ad}_sac"); bm.to_mesh(me); bm.free()
            o = bpy.data.objects.new(f"{ad}_sac", me); S.collection.objects.link(o); o.location = (X, Y, 0)
            o.modifiers.new("k", "SOLIDIFY").thickness = 0.08
            bv = o.modifiers.new("b", "BEVEL"); bv.width = 0.02; bv.segments = 3
            _set(o, HR, H, subsurf=1); o.rotation_euler[2] = math.radians(90 / 7)
        elif tur == "topuz":
            kure(f"{ad}_sac", (X, Y + 0.05, 2.25), (0.62, 0.55, 0.42), HR, H); kure(f"{ad}_topuz", (X, Y + 0.05, 2.72), (0.22, 0.22, 0.2), HR, H)
        elif tur == "kep":
            kure(f"{ad}_kep", (X, Y, 2.3), (0.62, 0.55, 0.38), HR, H); kutu(f"{ad}_siper", (X, Y - 0.62, 2.36), (0.3, 0.22, 0.03), HR, H, rot=(-8, 0, 0))
        elif tur == "kivircik":
            rnd = random.Random(len(ad))
            for i in range(22):
                a = rnd.uniform(0, 2 * math.pi); z = rnd.uniform(2.3, 2.62); r = 0.55 * math.sqrt(max(0.05, 1 - ((z - 2.06) / 0.62) ** 2))
                kure(f"{ad}_bukle", (X + math.cos(a) * r, Y + math.sin(a) * r * 0.9 + 0.04, z), (0.15, 0.15, 0.15), HR, H, 12)
        elif tur == "at_kuyrugu":
            kure(f"{ad}_sac", (X, Y + 0.05, 2.25), (0.62, 0.55, 0.42), HR, H); kure(f"{ad}_kuyruk", (X, Y + 0.6, 1.95), (0.14, 0.14, 0.35), HR, H)
        elif tur == "sapka":
            silindir(f"{ad}_sapka", (X, Y, 2.45), (X, Y, 2.85), 0.42, HR, H, uclar=False)
            silindir(f"{ad}_sapka_kenar", (X, Y, 2.44), (X, Y, 2.47), 0.7, HR, H, uclar=False)

    # --- görünürlük
    def gizli_baslat(self):
        for o in list(self.agiz.values()):
            gorunur(o, [(1, False)])
        gorunur(self._agiz_acik_objs(), [(1, False)])
        for s in (-1, 1):
            gorunur(self.yuz[s]["mutlu"], [(1, False)]); gorunur(self.yuz[s]["yarim"], [(1, False)])

    def _agiz_acik_objs(self):
        return [self.agiz_acik] + list(self.agiz_acik.children)

    # --- poz / ifade
    def poz(self, kare, ad, gecis=6):
        """Pozu kare'de tamamlar; gecis kare önceden (önceki pozdan) yumuşak geçer."""
        p = POZLAR[ad]
        if gecis:
            for o in (self.kol[1], self.kol[-1], self.kafa, self.govde): o.keyframe_insert("rotation_euler", frame=max(1, kare - gecis))
        anahtar(self.kol[1], kare, rot=p["S"]); anahtar(self.kol[-1], kare, rot=p["L"])
        anahtar(self.kafa, kare, rot=p["kafa"]); anahtar(self.govde, kare, rot=p["govde"])

    def ifade(self, kare, ad):
        f = IFADELER[ad]; self._ifade_kayit = getattr(self, "_ifade_kayit", []); self._ifade_kayit.append((kare, f["agiz"]))
        for k, o in self.agiz.items(): gorunur(o, [(kare, k == f["agiz"] and f["agiz"] != "acik")])
        gorunur(self._agiz_acik_objs(), [(kare, f["agiz"] == "acik")])
        if f["agiz"] == "acik": anahtar(self.agiz_acik, kare, olcek=1.0)
        for s in (-1, 1):
            y = self.yuz[s]; mutlu = f["goz"] == "mutlu"
            gorunur(y["goz"], [(kare, not mutlu)]); gorunur(y["parlama"], [(kare, not mutlu)]); gorunur(y["mutlu"], [(kare, mutlu)])
            gorunur(y["yarim"], [(kare, f["goz"] == "yarim")])
            g0 = self._goz_olcek[s]; k = 1.3 if f["goz"] == "buyuk" else 1.0
            y["goz"].keyframe_insert("scale", frame=max(1, kare - 3)); anahtar(y["goz"], kare, olcek=(g0[0] * k, g0[1], g0[2] * k))
            kp = y["kas"]; kp.keyframe_insert("location", frame=max(1, kare - 3)); kp.keyframe_insert("rotation_euler", frame=max(1, kare - 3))
            z0 = y["kas_z"]; kas = f["kas"]
            dz, rot = 0.0, 0.0
            if kas == "kalkik": dz = 0.035
            elif kas == "kizgin": dz, rot = -0.015, -18 * s
            elif kas == "uzgun": dz, rot = 0.01, 18 * s
            elif kas == "tek" and s == 1: dz, rot = 0.04, 12
            anahtar(kp, kare, loc=(kp.location.x, kp.location.y, z0 + dz), rot=(0, rot, 0))

    def bak(self, kare, yon=0, gecis=6):
        """Kafayı yana çevir (derece, + ekranda sola)."""
        self.kafa.keyframe_insert("rotation_euler", frame=max(1, kare - gecis))
        r = [math.degrees(a) for a in self.kafa.rotation_euler]; anahtar(self.kafa, kare, rot=(r[0], r[1], yon))

    def zipla(self, kare, yukseklik=0.35):
        x, y, z = self.kok.location
        anahtar(self.kok, kare - 4, loc=(x, y, z)); anahtar(self.govde, kare - 4, olcek=(1, 1, 1))
        anahtar(self.govde, kare, olcek=(1.06, 1.06, 0.92)); anahtar(self.kok, kare + 6, loc=(x, y, z + yukseklik))
        anahtar(self.govde, kare + 6, olcek=(0.96, 0.96, 1.06)); anahtar(self.kok, kare + 13, loc=(x, y, z))
        anahtar(self.govde, kare + 13, olcek=(1.07, 1.07, 0.9)); anahtar(self.govde, kare + 18, olcek=(1, 1, 1))

    def yuru(self, k0, k1, hedef_x, hedef_y=None):
        """k0..k1 arasında hedefe yürür (bacak salınımı + hafif zıplama)."""
        x0, y0, z0 = self.kok.location; hy = y0 if hedef_y is None else hedef_y
        anahtar(self.kok, k0, loc=(x0, y0, z0)); anahtar(self.kok, k1, loc=(hedef_x, hy, z0))
        adim = 7
        for i, k in enumerate(range(k0, k1 + 1, adim)):
            a = 25 if i % 2 == 0 else -25
            anahtar(self.bacak[1], k, rot=(a, 0, 0)); anahtar(self.bacak[-1], k, rot=(-a, 0, 0))
            anahtar(self.kol[1], k, rot=(-a * 0.8, -8, 0)); anahtar(self.kol[-1], k, rot=(a * 0.8, 8, 0))
        for o in (self.bacak[1], self.bacak[-1]): anahtar(o, k1 + 3, rot=(0, 0, 0))
        for s in (1, -1): anahtar(self.kol[s], k1 + 3, rot=(0, -8 * s, 0))
        self.kok.location = (hedef_x, hy, z0)
        if hedef_x != x0 or hy != y0:
            yon = math.degrees(math.atan2(hedef_x - x0, -(hy - y0))) if hy != y0 else (90 if hedef_x > x0 else -90)
            anahtar(self.kok, k0, rot=(0, 0, 0)); anahtar(self.kok, k0 + 4, rot=(0, 0, yon * 0.6))
            anahtar(self.kok, k1 - 2, rot=(0, 0, yon * 0.6)); anahtar(self.kok, k1 + 4, rot=(0, 0, 0))

    def isinlan(self, kare, x, y=0):
        """Kesme anında başka mekâna taşı (sabit geçiş)."""
        self.kok.keyframe_insert("location", frame=kare - 1)
        self.kok.location = (x, y, self.kok.location.z); self.kok.keyframe_insert("location", frame=kare)
        for fc in _fcurves(self.kok):
            if fc.data_path == "location":
                for kp in fc.keyframe_points:
                    if int(kp.co.x) in (kare - 1, kare): kp.interpolation = "CONSTANT"

    def nefes(self, k0, k1):
        for i, k in enumerate(range(k0, k1, FPS)):
            anahtar(self.govde, k, loc=(self.govde.location.x, self.govde.location.y, 0.95 + (0.012 if i % 2 else 0)))

    def konus(self, ses, t0, t1, esik=0.12):
        """Ses dosyasının t0..t1 saniyeleri arasında ağız sesle açılıp kapanır (dudak senkronu)."""
        env = ses_zarfi(ses)
        k0, k1 = sn(t0), sn(t1); acik_onceki = None
        kayit = sorted(getattr(self, "_ifade_kayit", []))
        def agiz_tipi(k):
            t = "gulus"
            for kk, a in kayit:
                if kk <= k: t = a
            return t
        for k in range(k0, k1 + 1):
            i = k - 1; v = env[i] if i < len(env) else 0.0
            acik = v > esik
            if acik:
                self.agiz_acik.scale = (0.75 + 0.25 * min(1, v), 1, 0.35 + 0.75 * min(1, v)); self.agiz_acik.keyframe_insert("scale", frame=k)
            if acik != acik_onceki:
                tip = agiz_tipi(k)
                gorunur(self._agiz_acik_objs(), [(k, acik or tip == "acik")])
                for ad_, o in self.agiz.items(): gorunur(o, [(k, (not acik) and ad_ == tip and tip != "acik")])
                acik_onceki = acik


def _fcurves(o):
    ad = o.animation_data
    if not ad or not ad.action: return []
    act = ad.action
    if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])): return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []): out.extend(cb.fcurves)
    return out


def karakter(ad, **kw):
    """Tahsin: karakter('tahsin', x=0). Yan karakter örneği:
       karakter('anne', x=1.4, sac='topuz', sac_renk='#5b3a1e', gomlek='#d35d6e', sort='#3d4f7a', kravat='#d35d6e', gozluk=False)"""
    return Karakter(ad, **kw)


# ------------------------------------------------------------------ ses
def ses_zarfi(yol):
    """Kare başına 0..1 ses yüksekliği (dudak senkronu için)."""
    tmp = "/tmp/_zarf.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", yol, "-ac", "1", "-ar", "16000", tmp], check=True)
    with wave.open(tmp) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    hop = 16000 // FPS; n = len(x) // hop
    r = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2)) for i in range(n)])
    r = r / (np.percentile(r, 95) + 1e-6)
    return np.clip(np.convolve(r, [0.25, 0.5, 0.25], mode="same"), 0, 1.2)


# ------------------------------------------------------------------ kamera
CEKIMLER = {  # (uzaklık, yükseklik, lens) — hedef karakterin göğüs/yüz hizası
    "genis": (7.2, 2.0, 32), "orta": (4.8, 1.75, 38), "yakin": (3.2, 2.15, 42), "asiri_yakin": (2.0, 2.15, 50),
    "alttan": (3.6, 0.6, 32), "ustten": (4.2, 4.2, 35),
}


def kamera_cek(kare, cekim="orta", hedef=(0, 0), aci=0.0, kesme=True, z_hedef=None, kaydir=(0, 0)):
    """Çekim koy. hedef: karakter ya da (x, y). aci: yatay açı (derece, + sağdan). kesme=False: önceki çekimden kayarak geçer.
       kaydir: (dx, dz) kadraj içi küçük kaydırma."""
    cam = S.camera
    if isinstance(hedef, Karakter):
        S.frame_set(kare); _upd(); hx, hy = hedef.kok.matrix_world.translation.x, hedef.kok.matrix_world.translation.y
    else: hx, hy = hedef
    uz, yk, lens = CEKIMLER[cekim]; a = math.radians(aci)
    loc = Vector((hx + math.sin(a) * uz + kaydir[0], hy - math.cos(a) * uz, yk + kaydir[1]))
    tz = z_hedef if z_hedef is not None else (1.55 if cekim in ("genis", "orta", "alttan") else 2.08)
    hedef_v = Vector((hx + kaydir[0] * 0.6, hy, tz))
    rot = (hedef_v - loc).to_track_quat("-Z", "Y").to_euler()
    if kesme and kare > 1:
        cam.keyframe_insert("location", frame=kare - 1); cam.keyframe_insert("rotation_euler", frame=kare - 1); cam.data.keyframe_insert("lens", frame=kare - 1)
    cam.location = loc; cam.rotation_euler = rot; cam.data.lens = lens
    cam.keyframe_insert("location", frame=kare); cam.keyframe_insert("rotation_euler", frame=kare); cam.data.keyframe_insert("lens", frame=kare)
    cam.data.dof.focus_distance = (hedef_v - loc).length; cam.data.keyframe_insert("dof.focus_distance", frame=kare)
    if kesme and kare > 1:
        for o in (cam, cam.data):
            for fc in _fcurves(o):
                for kp in fc.keyframe_points:
                    if int(round(kp.co.x)) == kare - 1: kp.interpolation = "CONSTANT"


def kamera_it(k0, k1, oran=0.85):
    """k0..k1 arasında kamera hedefe doğru yavaşça yaklaşır (oran<1) ya da uzaklaşır (oran>1)."""
    cam = S.camera; S.frame_set(k0); l0 = cam.location.copy(); r = cam.rotation_euler.copy()
    fwd = Vector((0, 0, -1)); fwd.rotate(r); d = 4.0 * (1 - oran)
    cam.keyframe_insert("location", frame=k0); cam.location = l0 + fwd * d; cam.keyframe_insert("location", frame=k1)


# ------------------------------------------------------------------ render
def kare_al(yol, kare):
    S.frame_set(kare); S.render.filepath = os.path.abspath(yol); bpy.ops.render.render(write_still=True)


def render_et(klasor, k0=None, k1=None):
    os.makedirs(klasor, exist_ok=True)
    if k0: S.frame_start = k0
    if k1: S.frame_end = k1
    S.render.image_settings.file_format = "PNG"; S.render.filepath = os.path.abspath(klasor) + "/f_"
    S.render.use_overwrite = False; S.render.use_placeholder = False   # yarıda kalırsa kaldığı yerden devam eder (son yarım kareyi sil)
    bpy.ops.render.render(animation=True)


def kaydet(yol):
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(yol))
