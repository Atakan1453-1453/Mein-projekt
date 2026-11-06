"""Drei Shorts (1080×1920) aus dem Verdun-Material: Hook in den ersten 2 s, große Untertitel.

  python3 shorts.py prep          Hook-/Outro-Stimmen aufbereiten (voice/S*.mp3 → .wav)
  python3 shorts.py still N t     Testbild von Short N zur Zeit t
  python3 shorts.py render N      Short N rendern → export/shorts/
"""
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

os.environ.setdefault("OMP_NUM_THREADS", "1")
import cv2  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

cv2.setNumThreads(1)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from warazlib.geo import Grid  # noqa: E402
from warazlib import compose as CP, fx as FX, ui as UI, audio as AU  # noqa: E402
import timeline as TL  # noqa: E402
import scenes as SC  # noqa: E402

MAPS = os.path.join(ROOT, "assets", "ww1", "maps", "verdun")
VOICE = os.path.join(HERE, "voice")
OUT = os.path.join(ROOT, "export", "shorts")
WORK = os.path.join(ROOT, "work", "shorts")
FPS = 30
W, H = 1080, 1920

# Untertitel (Anzeige-Schreibweise)
DISPLAY = {
    "S1": "Das größte Fort von Verdun. Erobert, ohne dass ein einziger Schuss fällt. 25. Februar 1916.",
    "S2": "Eine einzige Landstraße hat Frankreich gerettet. Verdun, Februar 1916. General Pétain soll die Stadt halten.",
    "S3": "Zehn Monate Hölle. Rund 300.000 Tote. Und am Ende fast kein Meter gewonnen.",
    "SO": "Die ganze Geschichte der Schlacht um Verdun siehst du auf WarAZ.",
    "P21": "Ein kleiner deutscher Trupp, etwa zehn Pioniere unter Feldwebel Kunze, arbeitet sich bei Schneetreiben an den Graben heran. Niemand schießt auf sie.",
    "P22": "Kunze klettert hinein. Die Gänge sind leer. Die kleine Restbesatzung hat sich vor dem Beschuss in die Tiefe zurückgezogen. Ranghöchster Franzose im Fort: ein Unteroffizier.",
    "P23": "Kurz darauf folgt Leutnant Radtke mit rund 20 Mann. Dann weitere Offiziere. Das stärkste Fort von Verdun wechselt den Besitzer. Ohne dass ein Schuss fällt.",
    "P24": "Den höchsten Orden bekommen übrigens nicht die Männer, die zuerst drin waren. Den Pour le Mérite erhält Oberleutnant von Brandis, der erst später kam.",
    "P27": "Sein größtes Problem ist nicht der Feind. Es ist der Nachschub. Die Bahnlinien nach Verdun sind abgeschnitten oder liegen unter Feuer. Übrig bleibt eine Landstraße. Von Bar-le-Duc nach Verdun. Gut 70 Kilometer.",
    "P28": "Pétain macht daraus eine Lebensader. Tausende Lastwagen fahren Tag und Nacht, in beide Richtungen. Zur Spitzenzeit rollt alle 14 Sekunden ein Fahrzeug vorbei. Das sind rund 6.000 am Tag.",
    "P29": "Die Straße hält das kaum aus. Tausende Männer schaufeln ohne Pause Schotter unter die Räder. Wer liegen bleibt, wird zur Seite geschoben. Die Kolonne darf nie stehen.",
    "P30": "Im April gibt ein Schriftsteller der Straße ihren Namen: Voie Sacrée. Die Heilige Straße.",
    "P41": "Inzwischen ist die Landschaft nicht mehr wiederzuerkennen. Die Wälder sind weg. Die Dörfer sind weg. Übrig ist ein Feld aus Trichtern. Trichter in Trichtern. Eine Mondlandschaft.",
    "P42": "Schätzungen zufolge fallen in zehn Monaten bis zu 60 Millionen Granaten auf dieses Gebiet. Mehr als zwei pro Sekunde. Tag und Nacht.",
    "P61": "Und jetzt schau dir die Karte an. Hier verlief die Front im Februar. Und hier verläuft sie im Dezember. Ein paar Kilometer. Mehr nicht.",
    "P62": "Dafür: rund 300.000 Tote. Genaue Zahlen gibt es bis heute nicht. Gängige Schätzungen sprechen von etwa 160.000 Franzosen und 140.000 Deutschen.",
    "P69": "Verdun war am Ende kein Kampf um Kilometer. Es war ein Kampf darum, wer zuerst aufgibt. Und keiner gab auf.",
}

SHORTS = {
    1: dict(name="verdun_short1_douaumont", title=["DIE STÄRKSTE FESTUNG", "FIEL FAST KAMPFLOS"], hook="S1",
            hook_vis=("P20", 0.0), paras=["P21", "P22", "P23", "P24"], km=0.55),
    2: dict(name="verdun_short2_heilige_strasse", title=["DIE STRASSE, DIE", "FRANKREICH RETTETE"], hook="S2",
            hook_vis=("P29", 0.0), paras=["P27", "P28", "P30"], km=0.55),
    3: dict(name="verdun_short3_kaum_gelaendegewinn", title=["10 MONATE HÖLLE,", "KAUM GELÄNDEGEWINN"], hook="S3",
            hook_vis=("P02", 0.0), paras=["P42", "P61", "P62", "P69"], km=0.62),
}


def wav_dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)


def plan(n, tl):
    """Abschnitte: (tau0, dauer, t_orig0, stimme, text-id)."""
    sh = SHORTS[n]
    segs = []
    tau = 0.0
    hd = wav_dur(os.path.join(VOICE, sh["hook"] + ".wav"))
    pid, f = sh["hook_vis"]
    a, b = tl[pid]
    segs.append(dict(tau0=tau, dur=hd + 0.45, t0=a + (b - a) * f, voice=sh["hook"], vo=0.12))
    tau += hd + 0.45
    for pid in sh["paras"]:
        a, b = tl[pid]
        d = wav_dur(os.path.join(VOICE, pid + ".wav"))
        segs.append(dict(tau0=tau, dur=d + 0.40, t0=a - 0.12, voice=pid, vo=0.12))
        tau += d + 0.40
    od = wav_dur(os.path.join(VOICE, "SO.wav"))
    last = segs[-1]
    segs.append(dict(tau0=tau, dur=od + 1.3, t0=last["t0"] + last["dur"], voice="SO", vo=0.1))
    tau += od + 1.3
    return segs, tau


# ---------------------------------------------------------------- Wort-Zeiten
def word_times(voice_id, text):
    """Wortzeiten (Start, Ende) relativ zum Dateianfang: Zeichenanteil ↔ Anteil der gesprochenen Zeit."""
    x = AU.read_wav(os.path.join(VOICE, voice_id + ".wav"))
    sr = AU.SR
    win = int(0.02 * sr)
    e = np.sqrt(np.convolve(x * x, np.ones(win) / win, mode="same"))
    voiced = e > 10 ** (-38 / 20)
    hop = int(0.01 * sr)
    v = voiced[::hop].astype(np.float32)
    cum = np.cumsum(v)
    total = cum[-1] if cum[-1] > 0 else 1.0
    words = text.split()
    w_len = np.array([len(w.strip(".,:;!?„“")) + 1.5 for w in words], np.float32)
    c = np.r_[0, np.cumsum(w_len)] / w_len.sum()
    out = []
    for i, w in enumerate(words):
        a = np.searchsorted(cum, c[i] * total) * 0.01
        b = np.searchsorted(cum, c[i + 1] * total) * 0.01
        out.append((w, a, max(a + 0.08, b)))
    return out


def chunks(wt, max_chars=16):
    """Wörter zu Untertitel-Häppchen (max. 3 Wörter / ~16 Zeichen, Satzende bricht)."""
    out, cur = [], []
    for w in wt:
        cur.append(w)
        txt = " ".join(x[0] for x in cur)
        if len(cur) >= 3 or len(txt) >= max_chars or w[0][-1] in ".!?:":
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


# ---------------------------------------------------------------- Overlay
def draw_short_overlay(img, n, tau, total, segs, subs):
    sh = SHORTS[n]
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    # Titel oben
    k = min(1.0, tau / 0.25)
    f = UI.font("title", 84)
    y = 150
    UI.plate(d, (60, y - 30, W - 60, y + 210), 0.92 * k, cut=20)
    for i, line in enumerate(sh["title"]):
        tw = UI.text_w(line, f, 2)
        UI.spaced(d, ((W - tw) / 2, y + i * 92), line, f, UI.STYLE["text"] + (int(255 * k),), 2)
    fl = UI.font("bold", 34)
    UI.plate(d, (60, y - 88, 60 + UI.text_w("VERDUN 1916", fl, 5) + 44, y - 40), 0.92 * k, cut=8)
    UI.spaced(d, (82, y - 84), "VERDUN 1916", fl, UI.STYLE["accent"] + (int(255 * k),), 5)
    # Untertitel
    for (c0, c1, words) in subs:
        if c0 <= tau < c1:
            fz = UI.font("title", 96)
            line = " ".join(w for (w, a, b) in words)
            tw = UI.text_w(line, fz, 1)
            x = (W - tw) / 2
            yy = 1390
            pad = 26
            d.rounded_rectangle((x - pad, yy - 14, x + tw + pad, yy + 112), radius=14, fill=(10, 10, 12, 175))
            cur = max([i for i, (w, a, b) in enumerate(words) if a <= tau] or [0])
            for i, (w, a, b) in enumerate(words):
                col = UI.STYLE["warn"] if i == cur else (250, 248, 240)
                d.text((x, yy), w, font=fz, fill=col + (255,), stroke_width=5, stroke_fill=(0, 0, 0, 255))
                x += d.textlength(w + " ", font=fz) + 1
            break
    # Abspann-Hinweis
    end = segs[-1]
    if tau >= end["tau0"]:
        k2 = min(1.0, (tau - end["tau0"]) / 0.4)
        UI.plate(d, (90, 1640, W - 90, 1800), k2, cut=16)
        msg = "GANZES VIDEO AUF WarAZ"
        fm = UI.font("title", 64)
        UI.spaced(d, ((W - UI.text_w(msg, fm, 2)) / 2, 1675), msg, fm, UI.STYLE["text"] + (int(255 * k2),), 2)
    # Fortschritt
    p = tau / total
    d.rectangle((0, H - 10, W * p, H), fill=UI.STYLE["accent"] + (230,))
    a = np.asarray(ov)
    fr = img.astype(np.float32)
    al = a[..., 3:4].astype(np.float32) / 255.0
    fr = fr * (1 - al) + a[..., :3].astype(np.float32) * al
    return np.clip(fr, 0, 255).astype(np.uint8)


_G = {}


def init(n):
    tl = TL.build()
    story = SC.build(tl)
    layers = {k: CP.Layer(MAPS, k, Grid.load(os.path.join(MAPS, f"{k}_grid.json")), W, H) for k in ("L3", "L2")}
    lib = FX.load_library(os.path.join(ROOT, "assets", "ww1", "fx"))
    comp = CP.Composer(story, layers, lib, SC.fronts(), W, H, FPS)
    comp.short_mode = True
    comp.km_scale = SHORTS[n]["km"]
    SC._OVL[0] = comp.ov
    segs, total = plan(n, tl)
    subs = []
    for sg in segs:
        wt = word_times(sg["voice"], DISPLAY[sg["voice"]])
        for ch in chunks(wt):
            a = sg["tau0"] + sg["vo"] + ch[0][1]
            b = sg["tau0"] + sg["vo"] + ch[-1][2] + 0.12
            subs.append((a, b, [(w, sg["tau0"] + sg["vo"] + wa, sg["tau0"] + sg["vo"] + wb) for (w, wa, wb) in ch]))
    # Lücken schließen (Untertitel bis zum nächsten stehen lassen, max. 0,4 s)
    for i in range(len(subs) - 1):
        a, b, w = subs[i]
        subs[i] = (a, min(subs[i + 1][0], b + 0.4), w)
    _G.update(C=comp, segs=segs, total=total, subs=subs, n=n, tl=tl)
    return comp


def frame_at(tau):
    C, segs = _G["C"], _G["segs"]
    sg = segs[-1]
    for s in segs:
        if s["tau0"] <= tau < s["tau0"] + s["dur"]:
            sg = s
            break
    t = sg["t0"] + (tau - sg["tau0"])
    img = C.frame(t)
    # kurze Weißblende an Abschnittsgrenzen (Schnitt)
    dt = tau - sg["tau0"]
    if dt < 0.12 and sg is not segs[0]:
        img = np.clip(img.astype(np.float32) + 90 * (1 - dt / 0.12), 0, 255).astype(np.uint8)
    img = draw_short_overlay(img, _G["n"], tau, _G["total"], segs, _G["subs"])
    if tau < 0.25:
        img = (img.astype(np.float32) * (tau / 0.25)).astype(np.uint8)
    return img


def render_part(args):
    n, k0, k1, path = args
    if not _G:
        init(n)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                          "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for i in range(k0, k1):
        p.stdin.write(frame_at(i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    return path


def audio_for(n):
    from scipy.io import wavfile
    tl = TL.build()
    segs, total = plan(n, tl)
    sr, music = wavfile.read(os.path.join(ROOT, "work", "audio", "music.wav"))
    sr, sfx = wavfile.read(os.path.join(ROOT, "work", "audio", "sfx.wav"))
    bed = (music.astype(np.float32) + sfx.astype(np.float32)) / 32768.0
    N = int((total + 0.5) * sr)
    out = np.zeros((N, 2), np.float32)
    fade = int(0.15 * sr)
    for sg in segs:
        a = int(sg["t0"] * sr)
        L = int(sg["dur"] * sr) + fade
        piece = bed[a:a + L].copy()
        env = np.ones(len(piece), np.float32)
        env[:fade] = np.linspace(0, 1, fade)
        env[-fade:] = np.linspace(1, 0, fade)
        piece *= env[:, None] * 0.9
        i0 = int(sg["tau0"] * sr)
        out[i0:i0 + len(piece)] += piece[:max(0, N - i0)]
        v = AU.read_wav(os.path.join(VOICE, sg["voice"] + ".wav"))
        j = int((sg["tau0"] + sg["vo"]) * sr)
        out[j:j + len(v), 0] += v[:max(0, N - j)] * 0.95
        out[j:j + len(v), 1] += v[:max(0, N - j)] * 0.95
    out = np.clip(out, -1, 1)
    path = os.path.join(WORK, f"short{n}_mix.wav")
    wavfile.write(path, sr, (out * 32767).astype(np.int16))
    return path, total


def main():
    cmd = sys.argv[1]
    if cmd == "prep":
        for sid in ("S1", "S2", "S3", "SO"):
            src = os.path.join(VOICE, sid + ".mp3")
            x = AU.load_any(src)
            sr = AU.SR
            win = int(0.02 * sr)
            e = np.sqrt(np.convolve(x * x, np.ones(win) / win, mode="same"))
            idx = np.nonzero(e > 10 ** (-42 / 20))[0]
            y = x[max(0, idx[0] - int(0.05 * sr)):idx[-1] + int(0.1 * sr)]
            tmp = os.path.join(VOICE, sid + "_raw.wav")
            AU.write_wav(tmp, y)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", "atempo=1.06", "-ar", "48000", "-ac", "1",
                            os.path.join(VOICE, sid + ".wav")], check=True)
            os.remove(tmp)
            print(sid, round(wav_dur(os.path.join(VOICE, sid + ".wav")), 2))
        return
    n = int(sys.argv[2])
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    if cmd == "still":
        init(n)
        for a in sys.argv[3:]:
            im = frame_at(float(a))
            cv2.imwrite(os.path.join(WORK, f"s{n}_t{float(a):05.1f}.jpg"), im[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 85])
        print("total", round(_G["total"], 1))
        return
    if cmd == "render":
        tl = TL.build()
        segs, total = plan(n, tl)
        nfr = int(total * FPS)
        parts = []
        step = int(math.ceil(nfr / 4))
        for j in range(4):
            parts.append((n, j * step, min(nfr, (j + 1) * step), os.path.join(WORK, f"s{n}_part{j}.mp4")))
        with Pool(4) as pool:
            files = pool.map(render_part, parts)
        lst = os.path.join(WORK, f"s{n}_list.txt")
        with open(lst, "w") as f:
            for p in files:
                f.write(f"file '{p}'\n")
        vid = os.path.join(WORK, f"s{n}_video.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
        wav, total = audio_for(n)
        out = os.path.join(OUT, SHORTS[n]["name"] + ".mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "256k",
                        "-shortest", "-movflags", "+faststart", out], check=True)
        print("fertig", out, round(total, 1), "s")


if __name__ == "__main__":
    main()
