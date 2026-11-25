#!/usr/bin/env python3
"""Seslendirmeyi kelime kelime zamanlar, altyazı üretir. Tamamen çevrimdışı (sherpa-onnx Whisper + Silero VAD).

Kullanım:
  python3 zamanla.py <ses dosyası> [--metin script.txt] [--cikti klasör] [--dil tr]

Çıktı (klasöre):
  words.json    [{"w": "kelime", "s": 0.12, "e": 0.48}, ...]   (cizgi-short / shorts-engine biçimi)
  phrases.json  [{"text": "...", "s":..., "e":..., "w0": i, "w1": j}, ...]
  altyazi.srt   cümle cümle altyazı
  transkript.txt  Whisper'ın duyduğu metin (metin verilmezse kelimeler buradan gelir)

Yöntem: Silero VAD konuşma parçalarını bulur, Whisper her parçayı ayrı tanır; parçanın
kelimeleri parça süresine hece sayısıyla dağıtılır; sonra senaryo kelimeleri tanınan
kelimelerle eşleştirilir. Müzikli seste de çalışır. Senaryo verilirse yazım senaryodan gelir.
"""
import argparse, difflib, json, os, re, shutil, subprocess, sys, tempfile, wave
import numpy as np

MODEL_DIR = os.environ.get("SHORTS_TOOLS_MODELS", os.path.expanduser("~/.cache/shorts-tools"))
SIZE = os.environ.get("WHISPER_SIZE", "small")
SR = 16000
VOW = set("aeıioöuüAEIİOÖUÜâîûy")


def syl(w):
    d = sum(ch.isdigit() for ch in w)
    if d:
        return 2 * d + 1
    return max(1, sum(1 for c in w if c in VOW))


def norm(w):
    return re.sub(r"[^\w]", "", w.replace("İ", "i").replace("I", "ı").lower())


def load(path):
    tmp = tempfile.mktemp(suffix=".wav")
    subprocess.run([shutil.which("ffmpeg") or "ffmpeg", "-v", "error", "-y", "-i", path,
                    "-ac", "1", "-ar", str(SR), tmp], check=True)
    with wave.open(tmp) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    os.remove(tmp)
    return x


def models_ok():
    d = os.path.join(MODEL_DIR, f"sherpa-onnx-whisper-{SIZE}")
    need = [os.path.join(d, f"{SIZE}-encoder.int8.onnx"), os.path.join(d, f"{SIZE}-decoder.int8.onnx"),
            os.path.join(d, f"{SIZE}-tokens.txt"), os.path.join(MODEL_DIR, "silero_vad.onnx")]
    missing = [p for p in need if not os.path.exists(p)]
    if missing:
        sys.exit("Model eksik: " + ", ".join(missing) + "\nÖnce: bash shorts-tools/kurulum.sh")
    return d


def speech_segments(x):
    import sherpa_onnx
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = os.path.join(MODEL_DIR, "silero_vad.onnx")
    cfg.silero_vad.min_silence_duration = 0.15
    cfg.silero_vad.min_speech_duration = 0.1
    cfg.silero_vad.max_speech_duration = 8
    cfg.sample_rate = SR
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=600)
    ws, segs = cfg.silero_vad.window_size, []
    def drain():
        while not vad.empty():
            segs.append((vad.front.start / SR, (vad.front.start + len(vad.front.samples)) / SR))
            vad.pop()
    for i in range(0, len(x), ws):
        vad.accept_waveform(x[i:i + ws]); drain()
    vad.flush(); drain()
    return segs


def recognize(x, segs, lang):
    import sherpa_onnx
    d = models_ok()
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=os.path.join(d, f"{SIZE}-encoder.int8.onnx"), decoder=os.path.join(d, f"{SIZE}-decoder.int8.onnx"),
        tokens=os.path.join(d, f"{SIZE}-tokens.txt"), language=lang, task="transcribe", num_threads=2)
    toks, texts = [], []
    for s, e in segs:
        a, b = max(0, int((s - 0.1) * SR)), min(len(x), int((e + 0.1) * SR))
        st = rec.create_stream(); st.accept_waveform(SR, x[a:b]); rec.decode_stream(st)
        words = [w for w in st.result.text.split() if norm(w)]
        texts.append(st.result.text.strip())
        if not words:
            continue
        wt = [syl(w) for w in words]; tot = sum(wt); acc = 0
        for w, k in zip(words, wt):
            t0 = s + (e - s) * acc / tot; acc += k; toks.append((w, t0, s + (e - s) * acc / tot))
    return toks, " ".join(t for t in texts if t)


def match(sw, toks):
    a = [norm(w) for w in sw]; b = [norm(t[0]) for t in toks]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    S = [None] * len(sw); E = [None] * len(sw)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            S[blk.a + k], E[blk.a + k] = toks[blk.b + k][1], toks[blk.b + k][2]
    n, i = len(sw), 0
    while i < n:
        if S[i] is not None:
            i += 1; continue
        j = i
        while j < n and S[j] is None:
            j += 1
        t0 = E[i - 1] if i > 0 else (toks[0][1] if toks else 0.0)
        t1 = S[j] if j < n else (toks[-1][2] if toks else t0 + 0.4 * (j - i))
        ws = [syl(sw[k]) for k in range(i, j)]; tot = sum(ws); acc = 0
        for k in range(i, j):
            S[k] = t0 + (t1 - t0) * acc / tot; acc += ws[k - i]; E[k] = t0 + (t1 - t0) * acc / tot
        i = j
    return [{"w": w, "s": round(float(s), 3), "e": round(float(e), 3)} for w, s, e in zip(sw, S, E)]


def phrases_of(words):
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        if re.search(r"[.!?…;:,]$", w["w"]) or i == len(words) - 1:
            out.append({"text": " ".join(words[j]["w"] for j in cur), "s": words[cur[0]]["s"],
                        "e": words[cur[-1]]["e"], "w0": cur[0], "w1": cur[-1]}); cur = []
    return out


def srt(words):
    def ts(t):
        h, m = int(t // 3600), int(t % 3600 // 60); s = t % 60
        return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s % 1) * 1000)) % 1000:03d}"
    lines, cur, n = [], [], 1
    for i, w in enumerate(words):
        cur.append(w)
        if re.search(r"[.!?…]$", w["w"]) or len(cur) >= 7 or i == len(words) - 1:
            lines.append(f"{n}\n{ts(cur[0]['s'])} --> {ts(cur[-1]['e'])}\n{' '.join(c['w'] for c in cur)}\n"); n += 1; cur = []
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ses"); ap.add_argument("--metin"); ap.add_argument("--cikti"); ap.add_argument("--dil", default="tr")
    a = ap.parse_args()
    out = a.cikti or os.path.dirname(os.path.abspath(a.ses)); os.makedirs(out, exist_ok=True)
    x = load(a.ses)
    segs = speech_segments(x)
    toks, heard = recognize(x, segs, a.dil)
    if a.metin:
        sw = [w for w in re.split(r"\s+", open(a.metin, encoding="utf-8").read().strip()) if w]
        words = match(sw, toks)
        hit = sum(1 for blk in difflib.SequenceMatcher(a=[norm(w) for w in sw], b=[norm(t[0]) for t in toks], autojunk=False).get_matching_blocks() for _ in range(blk.size))
        how = f"senaryonun %{round(100 * hit / max(1, len(sw)))}'i duyulan sesle eşleşti"
    else:
        words = [{"w": w, "s": round(s, 3), "e": round(e, 3)} for w, s, e in toks]; how = "senaryo yok, duyulan metin kullanıldı"
    ph = phrases_of(words)
    json.dump(words, open(os.path.join(out, "words.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    json.dump(ph, open(os.path.join(out, "phrases.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(out, "altyazi.srt"), "w", encoding="utf-8").write(srt(words))
    open(os.path.join(out, "transkript.txt"), "w", encoding="utf-8").write(heard + "\n")
    print(f"ses {len(x) / SR:.2f} sn · {len(segs)} konuşma parçası · {len(words)} kelime · {how}")
    for i, p in enumerate(ph):
        print(f"  P{i:02d} {p['s']:6.2f}-{p['e']:6.2f}  kare {round(p['s'] * 30):4d}-{round(p['e'] * 30):4d}  {p['text']}")


if __name__ == "__main__":
    main()
