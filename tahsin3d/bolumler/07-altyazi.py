import json, sys, re
P = sys.argv[1]
W = json.load(open(f"{P}/work/words.json")); PH = json.load(open(f"{P}/work/phrases.json"))
SURE = PH[-1]["e"] + 1.2
def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"
head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Alt,Archivo Black,90,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,1,0,1,7,4,2,70,70,470,1
Style: Baslik,Archivo Black,112,&H0033CCFF,&H0033CCFF,&H00000000,&H96000000,0,0,0,0,100,100,1,0,1,10,5,8,60,60,230,1
Style: Kart,Archivo Black,76,&H00FFFFFF,&H00FFFFFF,&H00703A1A,&H00703A1A,0,0,0,0,100,100,1,0,3,22,0,8,90,90,250,1
Style: Soru,Archivo Black,104,&H0033CCFF,&H0033CCFF,&H00000000,&H96000000,0,0,0,0,100,100,1,0,1,10,5,8,60,60,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ev = []
pop = r"{\fscx40\fscy40\t(0,180,\fscx112\fscy112)\t(180,300,\fscx100\fscy100)}"
ev.append(f"Dialogue: 1,{ts(0)},{ts(PH[1]['s'] - 0.2)},Baslik,,0,0,0,,Ya bulutlar pamuk\\Nşeker olsaydı?")
g = PH[13]["s"]; q = PH[16]["s"]
ev.append(f"Dialogue: 1,{ts(g)},{ts(q - 0.05)},Kart,,0,0,0,,{pop}GERÇEKTE...\\N{{\\c&H0033CCFF&}}Bir bulut yaklaşık\\N500 ton su taşır!")
ev.append(f"Dialogue: 1,{ts(q)},{ts(SURE)},Soru,,0,0,0,,{pop}Peki sen olsan\\Nne yapardın?")
# altyazı: cümleleri 2-4 kelimelik parçalara böl, söylenen kelime sarı
for pi, ph in enumerate(PH):
    if pi in (0, 16): continue
    ws = W[ph["w0"]:ph["w1"] + 1]
    parca, cur = [], []
    for w in ws:
        cur.append(w)
        if len(cur) >= 3 or re.search(r"[,.!?]$", w["w"]) or (len(cur) == 2 and len(" ".join(x["w"] for x in cur)) > 16):
            parca.append(cur); cur = []
    if cur:
        if len(cur) == 1 and parca and len(parca[-1]) < 4: parca[-1] += cur
        else: parca.append(cur)
    for pj, pc in enumerate(parca):
        son = parca[pj + 1][0]["s"] if pj + 1 < len(parca) else min(pc[-1]["e"] + 0.25, PH[pi + 1]["s"] if pi + 1 < len(PH) else 99)
        for k, w in enumerate(pc):
            a = w["s"] if k else pc[0]["s"]; b_ = pc[k + 1]["s"] if k + 1 < len(pc) else son
            txt = " ".join(("{\\c&H0033CCFF&\\fscx108\\fscy108}" + x["w"] + "{\\r}") if j == k else x["w"] for j, x in enumerate(pc))
            ev.append(f"Dialogue: 0,{ts(a)},{ts(b_)},Alt,,0,0,0,,{txt}")
open(f"{P}/work/yazilar.ass", "w").write(head + "\n".join(ev) + "\n")
print(len(ev), "olay")
