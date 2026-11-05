"""WarAZ-Einblendungen (einheitliches Design): Zähler, Ortslabel, Datumstitel, Zahlenkarte,
Kapitelkarte, Zitatkarte, Badge. Alles wird als RGBA-Ebene (PIL) gezeichnet und aufs Bild gelegt.

Stil: kantige Barlow-Condensed-Schrift, dunkle halbtransparente Platten mit abgeschrägter Ecke,
ein roter Akzentbalken. Farben siehe STYLE.
"""
import math
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "assets", "fonts")

STYLE = dict(
    text=(238, 233, 224),
    muted=(176, 172, 164),
    plate=(14, 16, 20),
    plate_alpha=200,
    accent=(200, 56, 38),        # Signalrot
    warn=(232, 184, 52),         # Gelb für „umstritten“/„Schätzung“
    de=(132, 136, 122),          # Feldgrau
    fr=(104, 138, 186),          # Horizontblau
)


@lru_cache(maxsize=64)
def font(name, size):
    files = {
        "title": "BarlowCondensed-ExtraBold.ttf",
        "bold": "BarlowCondensed-Bold.ttf",
        "semi": "BarlowCondensed-SemiBold.ttf",
        "med": "BarlowCondensed-Medium.ttf",
        "body": "Barlow-Medium.ttf",
    }
    return ImageFont.truetype(os.path.join(FONTS, files[name]), size)


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def fade(t, t0, t1, fin=0.35, fout=0.35):
    """Sichtbarkeit 0..1 für ein Element von t0 bis t1."""
    if t < t0 or t > t1:
        return 0.0
    return min(ease((t - t0) / fin) if fin > 0 else 1.0, ease((t1 - t) / fout) if fout > 0 else 1.0)


def spaced(draw, xy, text, fnt, fill, spacing=0.0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + spacing
    return x


def text_w(text, fnt, spacing=0.0):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    return sum(d.textlength(ch, font=fnt) + spacing for ch in text) - spacing


def plate(draw, box, alpha=1.0, cut=12, accent=True):
    x0, y0, x1, y1 = box
    a = int(STYLE["plate_alpha"] * alpha)
    poly = [(x0, y0), (x1 - cut, y0), (x1, y0 + cut), (x1, y1), (x0 + cut, y1), (x0, y1 - cut)]
    draw.polygon(poly, fill=STYLE["plate"] + (a,))
    if accent:
        draw.rectangle((x0, y0 + 6, x0 + 5, y1 - 6), fill=STYLE["accent"] + (int(255 * alpha),))


class Overlay:
    def __init__(self, W=1920, H=1080):
        self.W, self.H = W, H
        self.img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def clear(self):
        self.img = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    # ------------------------------------------------------------ Zähler (unten links, dauerhaft)
    def counter(self, date_text, day, alpha=1.0, x=56, y=None):
        if alpha <= 0:
            return
        y = self.H - 104 if y is None else y
        d = self.d
        f1, f2, f3 = font("semi", 34), font("bold", 34), font("med", 20)
        w1 = text_w(date_text, f1, 1.5)
        day_txt = f"TAG {day}"
        w2 = text_w(day_txt, f2, 1.5)
        W_ = 26 + w1 + 30 + w2 + 26
        plate(d, (x, y, x + W_, y + 58), alpha)
        a = int(255 * alpha)
        spaced(d, (x + 24, y + 9), date_text, f1, STYLE["text"] + (a,), 1.5)
        lx = x + 24 + w1 + 15
        d.line((lx, y + 14, lx, y + 44), fill=STYLE["muted"] + (int(160 * alpha),), width=2)
        spaced(d, (lx + 15, y + 9), day_txt, f2, STYLE["accent"] + (a,), 1.5)
        spaced(d, (x + 2, y - 26), "SCHLACHT UM VERDUN", f3, STYLE["muted"] + (int(200 * alpha),), 3)

    # ------------------------------------------------------------ Ortslabel (an einem Kartenpunkt)
    def place(self, text, ax, ay, p, side=1, sub=None, color=None):
        """p = Animationsfortschritt 0..1 (Einblenden) bzw. Sichtbarkeit."""
        if p <= 0:
            return
        d = self.d
        a = int(255 * min(1, p * 1.5))
        col = color or STYLE["text"]
        # Rautenmarker
        r = 7
        d.polygon([(ax, ay - r), (ax + r, ay), (ax, ay + r), (ax - r, ay)], fill=STYLE["accent"] + (a,),
                  outline=(255, 255, 255, a))
        # Führungslinie
        L = 46 * ease_out(min(1, p * 2))
        ex, ey = ax + side * L * 0.7, ay - L * 0.7
        d.line((ax, ay, ex, ey), fill=(255, 255, 255, int(a * 0.9)), width=2)
        if p < 0.3:
            return
        f = font("bold", 30)
        tw = text_w(text, f, 2.5)
        k = ease_out((p - 0.3) / 0.7)
        bw = (tw + 30) * k
        bx0 = ex if side > 0 else ex - bw
        by0 = ey - 22
        hsub = 24 if sub else 0
        plate(d, (bx0, by0 - hsub, bx0 + bw, by0 + 40), min(1, p), cut=9)
        if k > 0.6:
            ta = int(255 * ease((k - 0.6) / 0.4))
            tx = bx0 + 16
            spaced(d, (tx, by0 + 2), text, f, col + (ta,), 2.5)
            if sub:
                spaced(d, (tx, by0 - hsub + 2), sub, font("med", 18), STYLE["muted"] + (ta,), 2)

    # ------------------------------------------------------------ Datumstitel (Mitte)
    def date_title(self, big, small, p, y=None):
        if p <= 0:
            return
        d = self.d
        a = int(255 * p)
        y = self.H * 0.36 if y is None else y
        f = font("title", 104)
        tw = text_w(big, f, 4)
        x = (self.W - tw) / 2
        plate(d, (x - 210, y - 22, x + tw + 210, y + 186), p * 0.85, cut=18, accent=False)
        spaced(d, (x, y), big, f, STYLE["text"] + (a,), 4)
        L = 140 * ease_out(p)
        cy = y + 64
        d.line((x - 30 - L, cy, x - 30, cy), fill=STYLE["accent"] + (a,), width=4)
        d.line((x + tw + 30, cy, x + tw + 30 + L, cy), fill=STYLE["accent"] + (a,), width=4)
        if small:
            fs = font("semi", 40)
            sw = text_w(small, fs, 6)
            spaced(d, ((self.W - sw) / 2, y + 128), small, fs, STYLE["muted"] + (a,), 6)

    # ------------------------------------------------------------ Zahlenkarte
    def number_card(self, number, label, p, x=None, y=None, badge=None):
        if p <= 0:
            return
        d = self.d
        k = ease_out(p)
        fb, fl = font("title", 120), font("bold", 36)
        nw, lw = text_w(number, fb, 2), text_w(label, fl, 3)
        W_ = max(nw, lw) + 70
        x = self.W - W_ - 70 if x is None else x
        y = self.H * 0.30 if y is None else y
        x = x + (1 - k) * 60
        plate(d, (x, y, x + W_, y + 196), p, cut=16)
        a = int(255 * p)
        spaced(d, (x + 36, y + 10), number, fb, STYLE["text"] + (a,), 2)
        spaced(d, (x + 38, y + 140), label, fl, STYLE["accent"] + (a,), 3)
        if badge:
            self.badge(badge, x + 36, y - 40, p)

    def badge(self, text, x, y, p, color=None):
        d = self.d
        f = font("bold", 24)
        tw = text_w(text, f, 2)
        col = color or STYLE["warn"]
        a = int(255 * p)
        d.polygon([(x, y), (x + tw + 26, y), (x + tw + 34, y + 15), (x + tw + 26, y + 30), (x, y + 30)], fill=col + (a,))
        spaced(d, (x + 12, y + 1), text, f, (20, 18, 14, a), 2)

    # ------------------------------------------------------------ Kapitelkarte
    def chapter(self, num, title, p):
        if p <= 0:
            return
        d = self.d
        k = ease_out(p)
        fN, fT = font("title", 60), font("title", 66)
        txt = title.upper()
        tw = text_w(txt, fT, 3)
        x, y = 70, 70
        bw = (tw + 140) * k
        plate(d, (x, y, x + bw, y + 92), p, cut=14)
        if k > 0.5:
            a = int(255 * ease((k - 0.5) / 0.5))
            spaced(d, (x + 26, y + 8), str(num), fN, STYLE["accent"] + (a,), 0)
            spaced(d, (x + 90, y + 6), txt, fT, STYLE["text"] + (a,), 3)

    # ------------------------------------------------------------ Zitatkarte
    def quote(self, text, source, p, badge=None):
        if p <= 0:
            return
        d = self.d
        fq, fs = font("semi", 54), font("med", 26)
        lines = text.split("\n")
        tw = max(text_w(l, fq, 1) for l in lines)
        sw = text_w(source, fs, 1.5)
        W_ = max(tw, sw) + 90
        H_ = 70 * len(lines) + 90
        x = (self.W - W_) / 2
        y = self.H * 0.62 - H_ / 2
        plate(d, (x, y, x + W_, y + H_), p, cut=16)
        a = int(255 * p)
        d.text((x + 24, y - 6), "„", font=font("title", 90), fill=STYLE["accent"] + (a,))
        for i, l in enumerate(lines):
            spaced(d, (x + 56, y + 18 + i * 70), l, fq, STYLE["text"] + (a,), 1)
        spaced(d, (x + 58, y + H_ - 52), source, fs, STYLE["muted"] + (a,), 1.5)
        if badge:
            self.badge(badge, x + W_ - text_w(badge, font("bold", 24), 2) - 60, y - 40, p)

    # ------------------------------------------------------------ Ausgabe
    def rgba(self):
        return np.asarray(self.img)


def composite(frame, rgba):
    """frame: float32 RGB (0..255), rgba: uint8 HxWx4."""
    a = rgba[..., 3:4].astype(np.float32) / 255.0
    if not a.any():
        return frame
    ys, xs = np.nonzero(a[..., 0] > 0)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    sub = frame[y0:y1, x0:x1]
    aa = a[y0:y1, x0:x1]
    frame[y0:y1, x0:x1] = sub * (1 - aa) + rgba[y0:y1, x0:x1, :3].astype(np.float32) * aa
    return frame
