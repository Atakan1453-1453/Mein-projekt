"""YouTube-Vorschaubild (1280×720) aus der Render-Engine.

  python3 thumbnail.py                      → out/thumbnail.jpg
  python3 thumbnail.py --bg T LAT LON W P H  → nur Hintergrund zum Ausprobieren (out/thumb_bg.png)

Hintergrund: 18. März 1915 (Flotte, Minenfeld, Einschläge) mit eigener, steilerer Kamera und
ohne Beschriftungen; darauf Titel, Untertitel und die Flaggen beider Seiten.
"""
import argparse
import os

import numpy as np
import skia
from PIL import Image

import engine as E
import render
import scenes

OUT = os.environ.get("CNK_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
T_SCENE = 266.0
CAM = (40.035, 26.245, 15.0, 62.0, 33.0)
KEEP = (E.Ship, E.Mines, E.Fort, E.Battle, E.Explosion, E.Fire, E.Searchlight)
RED = skia.Color4f(0.80, 0.07, 0.09, 1)


def background(t, cam):
    tl = scenes.build()
    tl.objects = [o for o in tl.objects if isinstance(o, KEEP)]
    tl.cam = lambda _t: E.Cam(*cam)
    tl.dim = lambda _t: 0.0
    tl.global_fade = lambda _t: 1.0
    r = render.Renderer(tl)
    return r.frame(t)[..., :3].copy()


def flag_image(key, h):
    img = E.flag_texture(key)
    w = int(round(h * img.width() / img.height()))
    return img, w


def compose(bg):
    W, H = E.W, E.H
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    rgba = np.dstack([bg, np.full(bg.shape[:2], 255, np.uint8)])
    c.drawImage(skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType), 0, 0)
    # Farbe: etwas kühler und kontrastreicher, Ränder abdunkeln
    c.drawRect(skia.Rect.MakeWH(W, H), E.paint(skia.Color4f(0.02, 0.04, 0.08, 0.18)))
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H * 0.62)],
                                       [skia.Color4f(0, 0.01, 0.02, 0.86), skia.Color4f(0, 0.01, 0.02, 0)])
    p = skia.Paint()
    p.setShader(sh)
    c.drawRect(skia.Rect.MakeWH(W, H * 0.62), p)
    sh = skia.GradientShader.MakeLinear([skia.Point(0, H), skia.Point(0, H * 0.70)],
                                       [skia.Color4f(0, 0.01, 0.02, 0.80), skia.Color4f(0, 0.01, 0.02, 0)])
    p.setShader(sh)
    c.drawRect(skia.Rect.MakeLTRB(0, H * 0.70, W, H), p)
    E.Vignette().draw(c, 1.0)

    # Titel
    x0 = 80
    f_title = E.font("title", 214)
    E.draw_text(c, "ÇANAKKALE", x0 - 6, 262, f_title, E.c4(E.WHITE, 1), spacing=6, halo=10,
                halo_color=skia.Color4f(0, 0, 0, 0.55))
    wt = f_title.measureText("ÇANAKKALE") + 6 * 9
    f_year = E.font("title", 214)
    E.draw_text(c, "1915", x0 + wt + 34, 262, f_year, E.c4(E.GOLD, 1), spacing=6, halo=10,
                halo_color=skia.Color4f(0, 0, 0, 0.55))
    # Band
    band_txt = "DIE GANZE SCHLACHT AUF DER KARTE"
    f_band = E.font("cond_b", 64)
    bw = f_band.measureText(band_txt) + 4 * len(band_txt) + 64
    c.drawRect(skia.Rect.MakeXYWH(x0, 300, bw, 92), E.paint(RED))
    E.draw_text(c, band_txt, x0 + 32, 368, f_band, E.c4(E.WHITE, 1), spacing=4, shadow=False)

    # Flaggen: Verteidiger gegen Angreifer
    fh = 118
    y = H - 80 - fh

    def flag(key, x):
        img, w = flag_image(key, fh)
        r = skia.Rect.MakeXYWH(x, y, w, fh)
        c.drawRect(r.makeOutset(10, 10), E.paint(skia.Color4f(0, 0, 0, 0.35)))
        c.drawImageRect(img, r, E.SAMPLING)
        c.drawRect(r.makeOutset(3, 3), E.paint(E.c4(E.WHITE, 1), "stroke", 6))
        return x + w

    x = flag("tr", x0)
    f_vs = E.font("title", 92)
    E.draw_text(c, "VS", x + 46, y + fh / 2 + 33, f_vs, E.c4(E.GOLD, 1), halo=6, halo_color=skia.Color4f(0, 0, 0, 0.6))
    x += 46 + f_vs.measureText("VS") + 46
    for k in ("gb", "fr", "au", "nz"):
        x = flag(k, x) + 26

    # Kanal
    f_ch = E.font("cond_b", 46)
    E.draw_text(c, "WarAZ", W - 64, 92, f_ch, E.c4(E.WHITE, 0.92), "right", spacing=2, halo=5,
                halo_color=skia.Color4f(0, 0, 0, 0.6))
    c.drawRect(skia.Rect.MakeXYWH(W - 64 - f_ch.measureText("WarAZ") - 10, 106, f_ch.measureText("WarAZ") + 18, 4),
               E.paint(RED))

    buf = np.zeros((H, W, 4), np.uint8)
    surf.readPixels(skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType), buf)
    return Image.fromarray(buf[..., :3].copy()).resize((1280, 720), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bg", nargs=6, type=float, default=None)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.bg:
        t, cam = a.bg[0], tuple(a.bg[1:])
        Image.fromarray(background(t, cam)).resize((960, 540)).save(os.path.join(OUT, "thumb_bg.png"))
        return
    img = compose(background(T_SCENE, CAM))
    p = os.path.join(OUT, "thumbnail.jpg")
    img.save(p, quality=92)
    print(p, os.path.getsize(p), "Bytes")


if __name__ == "__main__":
    main()
