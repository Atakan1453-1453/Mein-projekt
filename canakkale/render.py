"""Rendert das Video (ohne Ton) parallel in Teilstücken und fügt sie zusammen.

  python3 render.py --stills 0,60,300        Einzelbilder (Sekunden) nach out/stills/
  python3 render.py --contact                Kontaktbogen: je Szene ein Bild
  python3 render.py --from 0 --to 30         Ausschnitt rendern (Sekunden)
  python3 render.py                          komplettes Video → out/canakkale_video.mp4
"""
import argparse
import math
import os
import subprocess
import sys
import time
from multiprocessing import Process

import numpy as np
import skia

import engine as E

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("CNK_OUT", os.path.join(HERE, "out"))


class Renderer:
    def __init__(self, timeline):
        self.tl = timeline
        self.europe = E.MapLayer("europe")
        self.L2 = E.MapLayer("sat_L2", feather=40)
        self.L3 = E.MapLayer("sat_L3", feather=160)
        self.vignette = E.Vignette()
        self.surface = skia.Surface(E.W, E.H)
        self.buf = np.zeros((E.H, E.W, 4), np.uint8)

    def draw_layer(self, c, v, layer, paint=None):
        """Nur den sichtbaren Teil der Karte zeichnen (vermeidet Punkte hinter der Kamera)."""
        img = layer.image
        Ai = np.linalg.inv(layer.A)
        us, vs = [], []
        for sx in (0, E.W / 2, E.W):
            for sy in (0, E.H / 2, E.H):
                X, Y = v.unproject(sx, sy)
                u, w_, _ = Ai @ np.array([X, Y, 1.0])
                us.append(u)
                vs.append(w_)
        mx = (max(us) - min(us)) * 0.04 + 8
        my = (max(vs) - min(vs)) * 0.04 + 8
        x0, x1 = max(0, min(us) - mx), min(img.width(), max(us) + mx)
        y0, y1 = max(0, min(vs) - my), min(img.height(), max(vs) + my)
        if x1 <= x0 or y1 <= y0:
            return
        r = skia.Rect.MakeLTRB(x0, y0, x1, y1)
        c.save()
        c.concat(v.skmatrix(layer.A))
        c.drawImageRect(img, r, r, E.SAMPLING, paint, skia.Canvas.kFast_SrcRectConstraint)
        c.restore()

    def draw_base(self, c, v, t):
        cam = v.cam
        c.clear(skia.Color4f(0.04, 0.07, 0.095, 1))
        samp = E.SAMPLING
        sat = E.clamp((1100 - cam.width) / 700)
        l3 = sat * E.clamp((140 - cam.width) / 40) if cam.width < 140 else 0.0
        need_l2 = not (l3 >= 1 and v.covered_by(self.L3.bounds, 200))
        need_eu = not (sat >= 1 and v.covered_by(self.L2.bounds, 60))
        if need_eu and need_l2:
            self.draw_layer(c, v, self.europe)
        if sat > 0:
            p = skia.Paint()
            p.setAlphaf(sat)
            if need_l2:
                self.draw_layer(c, v, self.L2, p)
            if l3 > 0:
                p3 = skia.Paint()
                p3.setAlphaf(l3)
                self.draw_layer(c, v, self.L3, p3)
        if sat > 0:
            c.drawRect(skia.Rect.MakeWH(E.W, E.H), E.paint(skia.Color4f(0.0, 0.01, 0.02, 0.12 * sat)))
        # Atmosphäre bei schräger Kamera
        if cam.pitch > 5:
            k = E.clamp((cam.pitch - 5) / 45)
            sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, E.H * 0.55)],
                                               [skia.Color4f(0.62, 0.70, 0.78, 0.55 * k), skia.Color4f(0.62, 0.70, 0.78, 0)])
            pp = skia.Paint()
            pp.setShader(sh)
            c.drawRect(skia.Rect.MakeWH(E.W, E.H * 0.55), pp)
        dim = self.tl.dim(t)
        if dim > 0:
            c.drawRect(skia.Rect.MakeWH(E.W, E.H), E.paint(skia.Color4f(0.0, 0.01, 0.02, dim)))

    def frame(self, t):
        cam = self.tl.cam(t)
        v = E.View(cam)
        c = self.surface.getCanvas()
        self.draw_base(c, v, t)
        objs = [o for o in self.tl.objects if o.t0 - 0.05 <= t <= o.t1 + 0.05]
        objs.sort(key=lambda o: o.z)
        for o in objs:
            if o.z >= 50:
                continue
            o.draw(c, v, t)
        self.vignette.draw(c, 1.0)
        for o in objs:
            if o.z >= 50:
                o.draw(c, v, t)
        g = self.tl.global_fade(t)
        if g < 1:
            c.drawRect(skia.Rect.MakeWH(E.W, E.H), E.paint(skia.Color4f(0, 0, 0, 1 - g)))
        self.surface.readPixels(skia.ImageInfo.Make(E.W, E.H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType), self.buf)
        return self.buf


def ffmpeg_writer(path, crf=21):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{E.W}x{E.H}",
           "-r", str(E.FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-tune", "film",
           "-pix_fmt", "yuv420p", "-threads", "2", path]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def render_range(f0, f1, path, worker=0):
    import scenes
    tl = scenes.build()
    r = Renderer(tl)
    w = ffmpeg_writer(path)
    t_start = time.time()
    for i in range(f0, f1):
        buf = r.frame(i / E.FPS)
        w.stdin.write(buf.tobytes())
        if (i - f0) % 300 == 0 and i > f0:
            el = time.time() - t_start
            print(f"[w{worker}] {i - f0}/{f1 - f0} Frames, {el / (i - f0) * 1000:.0f} ms/Frame", flush=True)
    w.stdin.close()
    w.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", default=None)
    ap.add_argument("--contact", action="store_true")
    ap.add_argument("--from", dest="t0", type=float, default=0)
    ap.add_argument("--to", dest="t1", type=float, default=None)
    ap.add_argument("--workers", type=int, default=3)  # je Prozess ca. 3,6 GB RAM
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    import scenes
    tl = scenes.build()
    if a.stills or a.contact:
        from PIL import Image
        r = Renderer(tl)
        d = os.path.join(OUT, "stills")
        os.makedirs(d, exist_ok=True)
        if a.contact:
            times = [s + min(8.0, d_ * 0.6) for s, d_ in tl.scene_starts()]
        else:
            times = [float(x) for x in a.stills.split(",")]
        paths = []
        for tt in times:
            t0 = time.time()
            img = r.frame(tt)
            p = os.path.join(d, f"still_{tt:07.1f}.png")
            Image.fromarray(img[..., :3].copy()).save(p)
            paths.append(p)
            print(p, f"{(time.time() - t0) * 1000:.0f} ms", flush=True)
        if a.contact:
            ims = [Image.open(p).resize((480, 270)) for p in paths]
            cols = 4
            rows = math.ceil(len(ims) / cols)
            sheet = Image.new("RGB", (cols * 480, rows * 270))
            for i, im in enumerate(ims):
                sheet.paste(im, ((i % cols) * 480, (i // cols) * 270))
            sheet.save(os.path.join(OUT, "kontaktbogen.jpg"), quality=88)
        return
    t1 = a.t1 if a.t1 is not None else tl.duration
    f0, f1 = int(a.t0 * E.FPS), int(t1 * E.FPS)
    n = a.workers
    parts = []
    procs = []
    chunk = math.ceil((f1 - f0) / n)
    for k in range(n):
        s, e = f0 + k * chunk, min(f1, f0 + (k + 1) * chunk)
        if s >= e:
            continue
        p = os.path.join(OUT, f"part_{k:02d}.mp4")
        parts.append(p)
        pr = Process(target=render_range, args=(s, e, p, k))
        pr.start()
        procs.append(pr)
    for pr in procs:
        pr.join()
    lst = os.path.join(OUT, "parts.txt")
    with open(lst, "w") as fh:
        for p in parts:
            fh.write(f"file '{p}'\n")
    out = a.out or os.path.join(OUT, "canakkale_video.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    print("fertig:", out)


if __name__ == "__main__":
    main()
