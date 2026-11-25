#!/usr/bin/env python3
"""Render karelerini seslendirme + müzik + efektlerle 1080x1920 MP4'e birleştirir, sesi -14 LUFS'a çeker.

python3 bitir.py <proje_klasoru> <cikti.mp4>

Gerekli: <proje>/work/kareler/f_0001.png ...  ve  <proje>/work/voice.wav
İsteğe bağlı: <proje>/work/ses.json
  {"muzik": "work/sfx/muzik.wav", "muzik_seviye": 0.22,
   "efektler": [{"dosya": "work/sfx/boing.wav", "sn": 4.1, "seviye": 0.9, "sure": 2.5}, ...]}   (sure: en fazla kaç sn çalsın)
  Efektleri earshot ile üret:  earshot make "a cartoon boing when a character jumps" -o work/sfx/boing.wav
"""
import json, os, re, subprocess, sys

FPS = int(os.environ.get("FPS", "24"))
P = os.path.abspath(sys.argv[1]); OUT = os.path.abspath(sys.argv[2]); W = os.path.join(P, "work")
K = os.path.join(W, "kareler")
n = len([f for f in os.listdir(K) if re.match(r"f_\d{4}\.png$", f)])
first = min(int(f[2:6]) for f in os.listdir(K) if re.match(r"f_\d{4}\.png$", f))
dur = n / FPS
ofs = (first - 1) / FPS   # kareler 1'den başlamıyorsa (parça render) ses de oradan başlar
cfg = json.load(open(os.path.join(W, "ses.json"))) if os.path.exists(os.path.join(W, "ses.json")) else {}

def p(x): return x if os.path.isabs(x) else os.path.join(P, x)

ins = ["-framerate", str(FPS), "-start_number", str(first), "-i", os.path.join(K, "f_%04d.png"), "-ss", f"{ofs:.3f}", "-i", os.path.join(W, "voice.wav")]
fl = [f"[0:v]scale=1080:1920:flags=lanczos,unsharp=5:5:0.6,format=yuv420p[v]", "[1:a]volume=1.0[ses]"]
mix = ["[ses]"]; i = 2
if cfg.get("muzik"):
    ins += ["-stream_loop", "-1", "-i", p(cfg["muzik"])]
    fl.append(f"[{i}:a]volume={cfg.get('muzik_seviye', 0.22)},atrim=0:{dur:.2f},afade=t=in:d=0.5,afade=t=out:st={max(0, dur - 1):.2f}:d=1[m]"); mix.append("[m]"); i += 1
for j, ef in enumerate(cfg.get("efektler", [])):
    ms = int((ef["sn"] - ofs) * 1000)
    if ms < 0 or ms > dur * 1000: continue
    ins += ["-i", p(ef["dosya"])]
    sure = ef.get("sure", 2.5)
    fl.append(f"[{i}:a]atrim=0:{sure},afade=t=out:st={max(0, sure - 0.3)}:d=0.3,adelay={ms}|{ms},volume={ef.get('seviye', 0.8)}[e{j}]"); mix.append(f"[e{j}]"); i += 1
fl.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=longest,apad,atrim=0:{dur:.3f}[a0]")
tmp = OUT + ".tmp.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fl), "-map", "[v]", "-map", "[a0]",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", tmp], check=True)
# iki geçişli ses seviyesi: -14 LUFS, tepe -1 dBTP
r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", tmp, "-vn", "-af", "loudnorm=I=-14:TP=-1:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
L = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S).group(0))
af = (f"loudnorm=I=-14:TP=-1:LRA=11:measured_I={L['input_i']}:measured_TP={L['input_tp']}:measured_LRA={L['input_lra']}:"
      f"measured_thresh={L['input_thresh']}:offset={L['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-movflags", "+faststart", OUT], check=True)
os.remove(tmp)
print(f"{OUT}: {n} kare, {dur:.2f} sn, {os.path.getsize(OUT) / 1e6:.1f} MB (ses girişi {L['input_i']} LUFS)")
