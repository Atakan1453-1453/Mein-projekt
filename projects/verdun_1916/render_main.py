"""Rendert das Hauptvideo in Abschnitten (abbruchsicher) und setzt es zusammen.

  python3 render_main.py stills [t1 t2 …]     Einzelbilder nach work/stills/
  python3 render_main.py sheet                 je ein Bild pro Absatz (Kontaktbögen)
  python3 render_main.py video [--workers 4]   Abschnitte nach work/segments/, dann work/video_noaudio.mp4
"""
import json
import os
import subprocess
import sys
import time
from multiprocessing import Pool

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import cv2  # noqa: E402
import numpy as np  # noqa: E402

cv2.setNumThreads(1)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from warazlib.geo import Grid  # noqa: E402
from warazlib import compose as CP, fx as FX  # noqa: E402
import timeline as TL  # noqa: E402
import scenes as SC  # noqa: E402

MAPS = os.path.join(ROOT, "assets", "ww1", "maps", "verdun")
WORK = os.path.join(ROOT, "work")
FPS = 30
W, H = 1920, 1080
SEG = 10.0            # Sekunden pro Abschnitt
_G = {}


def init(w=W, h=H):
    tl = TL.build()
    story = SC.build(tl)
    layers = {k: CP.Layer(MAPS, k, Grid.load(os.path.join(MAPS, f"{k}_grid.json")), w, h) for k in ("L3", "L2")}
    lib = FX.load_library(os.path.join(ROOT, "assets", "ww1", "fx"))
    comp = CP.Composer(story, layers, lib, SC.fronts(), w, h, FPS)
    SC._OVL[0] = comp.ov
    _G.update(tl=tl, S=story, C=comp)
    return comp


def render_segment(k):
    C = _G["C"]
    S = _G["S"]
    out = os.path.join(WORK, "segments", f"seg_{k:04d}.mp4")
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        return k, 0.0
    t0 = k * SEG
    n = int(round(min(SEG, S.duration - t0) * FPS))
    tmp = out + ".part.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                          "-pix_fmt", "yuv420p", "-g", "60", tmp], stdin=subprocess.PIPE)
    st = time.time()
    for i in range(n):
        t = t0 + i / FPS
        p.stdin.write(C.frame(t).tobytes())
    p.stdin.close()
    p.wait()
    os.replace(tmp, out)
    return k, (time.time() - st) / max(1, n)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "video"
    if mode == "stills":
        C = init()
        os.makedirs(os.path.join(WORK, "stills"), exist_ok=True)
        for a in sys.argv[2:]:
            t = float(a)
            st = time.time()
            im = C.frame(t)
            cv2.imwrite(os.path.join(WORK, "stills", f"t{t:07.2f}.jpg"), im[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
            print("t", t, round(time.time() - st, 2), "s", flush=True)
        return
    if mode == "sheet":
        C = init()
        tl = _G["tl"]
        os.makedirs(os.path.join(WORK, "sheet"), exist_ok=True)
        ids = sys.argv[2:] or list(tl.keys())
        for pid in ids:
            a, b = tl[pid]
            t = a + (b - a) * 0.6
            im = C.frame(t)
            im = cv2.resize(im, (640, 360), interpolation=cv2.INTER_AREA)
            cv2.putText(im, f"{pid} {t:.1f}s", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.imwrite(os.path.join(WORK, "sheet", f"{pid}.jpg"), im[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 80])
            print(pid, flush=True)
        return
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    os.makedirs(os.path.join(WORK, "segments"), exist_ok=True)
    tl = TL.build()
    dur = SC.build(tl).duration
    nseg = int(np.ceil(dur / SEG))
    todo = [k for k in range(nseg) if not os.path.exists(os.path.join(WORK, "segments", f"seg_{k:04d}.mp4"))]
    print("Abschnitte", nseg, "offen", len(todo), "Dauer", round(dur, 1), flush=True)
    st = time.time()
    with Pool(workers, initializer=init) as pool:
        for j, (k, spf) in enumerate(pool.imap_unordered(render_segment, todo)):
            print(f"Abschnitt {k} fertig ({spf:.2f} s/Bild), {j + 1}/{len(todo)}, {time.time() - st:.0f} s", flush=True)
    lst = os.path.join(WORK, "segments", "list.txt")
    with open(lst, "w") as f:
        for k in range(nseg):
            f.write(f"file 'seg_{k:04d}.mp4'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    os.path.join(WORK, "video_noaudio.mp4")], check=True)
    print("fertig", os.path.join(WORK, "video_noaudio.mp4"))


if __name__ == "__main__":
    main()
