#!/usr/bin/env python3
"""Rendert das 60-Sekunden-Präsentationsvideo „Galerie Königshof Mettmann“.

Format: 1920x1080, 30 fps, H.264 + AAC.

Aufruf:
    python3 video/render.py                 # komplettes Video nach output/
    python3 video/render.py --preview       # nur Standbilder je Szene (schnell)

Eigene Fotos: Legt man Bilder nach assets/photos/ (Dateiname beginnt mit dem
Szenen-Schlüssel, z. B. "intro.jpg", "shops_1.jpg"), werden sie automatisch als
Hintergrund mit Ken-Burns-Effekt verwendet. Schlüssel: intro, lage, zahlen,
geschichte, shops, parken, zeiten, outro.
"""
import argparse
import glob
import math
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content as C  # noqa: E402

W, H = 1920, 1080
FPS = 30
DURATION = 60.0
NFRAMES = int(FPS * DURATION)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHOTO_DIR = os.path.join(ROOT, "assets", "photos")
OUT_DIR = os.path.join(ROOT, "output")

# Farbwelt: tiefes Nachtblau + Gold („Königshof“)
BG_TOP = np.array([16, 26, 46], dtype=np.float32)
BG_BOT = np.array([5, 9, 18], dtype=np.float32)
GOLD = (214, 178, 106)
GOLD_LIGHT = (242, 216, 160)
WHITE = (246, 243, 236)
MUTED = (170, 178, 196)

FONTS = {
    "serif": ["/usr/share/fonts/truetype/crosextra/Caladea-Regular.ttf", "DejaVuSerif.ttf"],
    "serif_bold": ["/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf", "DejaVuSerif-Bold.ttf"],
    "serif_italic": ["/usr/share/fonts/truetype/crosextra/Caladea-Italic.ttf", "DejaVuSerif.ttf"],
    "sans": ["/usr/share/fonts/opentype/inter/Inter-Regular.otf", "DejaVuSans.ttf"],
    "sans_light": ["/usr/share/fonts/opentype/inter/Inter-Light.otf", "DejaVuSans.ttf"],
    "sans_medium": ["/usr/share/fonts/opentype/inter/Inter-Medium.otf", "DejaVuSans.ttf"],
    "sans_semibold": ["/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", "DejaVuSans-Bold.ttf"],
    "display_bold": ["/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", "DejaVuSans-Bold.ttf"],
}

SS = 4  # Supersampling für glatte Formen


# --------------------------------------------------------------------------
# Hilfsfunktionen: Easing, Fonts, Sprites
# --------------------------------------------------------------------------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def prog(t, start, dur=0.7):
    """Animationsfortschritt 0..1 (ease-out) ab `start` über `dur` Sekunden."""
    return ease_out((t - start) / dur)


def out_fade(t, dur, length=0.45):
    """1 während der Szene, blendet in den letzten `length` Sekunden auf 0."""
    return ease_in_out((dur - t) / length)


@lru_cache(maxsize=None)
def font(key, size):
    for path in FONTS[key]:
        try:
            return ImageFont.truetype(path, int(size))
        except OSError:
            continue
    return ImageFont.load_default(size=int(size))


@lru_cache(maxsize=8192)
def text_sprite(text, key, size, color, tracking=0):
    f = font(key, size)
    asc, desc = f.getmetrics()
    pad = 8
    if tracking:
        widths = [f.getlength(ch) for ch in text]
        tw = sum(widths) + tracking * (len(text) - 1)
    else:
        tw = f.getlength(text)
    img = Image.new("RGBA", (int(math.ceil(tw)) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if tracking:
        x = pad
        for ch, wch in zip(text, widths):
            d.text((x, pad), ch, font=f, fill=color + (255,))
            x += wch + tracking
    else:
        d.text((pad, pad), text, font=f, fill=color + (255,))
    return img


def fit_text(text, key, size, color, max_w, tracking=0):
    spr = text_sprite(text, key, size, color, tracking)
    while spr.width > max_w and size > 10:
        size -= 2
        spr = text_sprite(text, key, size, color, tracking)
    return spr


def with_alpha(img, a):
    if a >= 0.999:
        return img
    r, g, b, al = img.split()
    lut = [int(v * a) for v in range(256)]
    return Image.merge("RGBA", (r, g, b, al.point(lut)))


def blit(frame, spr, x, y, alpha=1.0, anchor="c", scale=1.0):
    if alpha <= 0.004:
        return
    if abs(scale - 1.0) > 1e-3:
        spr = spr.resize((max(1, int(spr.width * scale)), max(1, int(spr.height * scale))), Image.BICUBIC)
    spr = with_alpha(spr, alpha)
    if anchor == "c":
        x0, y0 = x - spr.width / 2, y - spr.height / 2
    elif anchor == "l":
        x0, y0 = x, y - spr.height / 2
    else:  # "r"
        x0, y0 = x - spr.width, y - spr.height / 2
    x0, y0 = int(round(x0)), int(round(y0))
    # auf Bildgrenzen zuschneiden
    sx0, sy0 = max(0, -x0), max(0, -y0)
    sx1, sy1 = min(spr.width, W - x0), min(spr.height, H - y0)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    if (sx0, sy0, sx1, sy1) != (0, 0, spr.width, spr.height):
        spr = spr.crop((sx0, sy0, sx1, sy1))
    frame.alpha_composite(spr, (x0 + sx0, y0 + sy0))


def supersampled(w, h, draw_fn):
    big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(big), SS)
    return big.resize((w, h), Image.LANCZOS)


@lru_cache(maxsize=None)
def crown_sprite(scale=1.0):
    w, h = int(240 * scale), int(170 * scale)

    def draw(d, s):
        k = s * scale
        pts = [(30, 118), (18, 42), (76, 86), (120, 14), (164, 86), (222, 42), (210, 118)]
        d.polygon([(x * k, y * k) for x, y in pts], fill=GOLD + (255,))
        for cx, cy in [(18, 42), (120, 14), (222, 42)]:
            r = 10 * k
            d.ellipse((cx * k - r, cy * k - r, cx * k + r, cy * k + r), fill=GOLD_LIGHT + (255,))
        d.rounded_rectangle((28 * k, 128 * k, 212 * k, 152 * k), radius=5 * k, fill=GOLD + (255,))
        r = 7 * k
        d.ellipse((120 * k - r, 140 * k - r, 120 * k + r, 140 * k + r), fill=(16, 26, 46, 255))

    return supersampled(w, h, draw)


@lru_cache(maxsize=None)
def dot_sprite(radius, color, ring=0):
    size = int(radius * 2 + 4)

    def draw(d, s):
        c = size * s / 2
        r = radius * s
        if ring:
            d.ellipse((c - r, c - r, c + r, c + r), outline=color + (255,), width=int(ring * s))
        else:
            d.ellipse((c - r, c - r, c + r, c + r), fill=color + (255,))

    return supersampled(size, size, draw)


@lru_cache(maxsize=None)
def pin_sprite():
    w, h = 96, 128

    def draw(d, s):
        cx, cy, r = 48 * s, 46 * s, 40 * s
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GOLD + (255,))
        d.polygon([(cx - 34 * s, cy + 22 * s), (cx + 34 * s, cy + 22 * s), (cx, 124 * s)], fill=GOLD + (255,))
        ri = 15 * s
        d.ellipse((cx - ri, cy - ri, cx + ri, cy + ri), fill=(12, 20, 36, 255))

    return supersampled(w, h, draw)


@lru_cache(maxsize=None)
def check_sprite():
    size = 60

    def draw(d, s):
        d.ellipse((3 * s, 3 * s, 57 * s, 57 * s), outline=GOLD + (255,), width=3 * s)
        d.line([(18 * s, 31 * s), (27 * s, 40 * s), (43 * s, 22 * s)], fill=GOLD_LIGHT + (255,), width=5 * s, joint="curve")

    return supersampled(size, size, draw)


@lru_cache(maxsize=None)
def panel_sprite(w, h, radius=18, fill_a=16, border_a=110, border=2):
    def draw(d, s):
        d.rounded_rectangle((s, s, w * s - s, h * s - s), radius=radius * s,
                            fill=(255, 255, 255, fill_a), outline=GOLD + (border_a,), width=border * s)

    return supersampled(w, h, draw)


@lru_cache(maxsize=None)
def label_pill(text, key, size, color):
    spr = text_sprite(text, key, size, color)
    w, h = spr.width + 28, spr.height + 4

    def draw(d, s):
        d.rounded_rectangle((0, 0, w * s - 1, h * s - 1), radius=h * s // 2, fill=(12, 20, 36, 235),
                            outline=GOLD + (90,), width=2 * s)

    img = supersampled(w, h, draw)
    img.alpha_composite(spr, (14, 2))
    return img


@lru_cache(maxsize=None)
def parking_sprite():
    size = 300

    def draw(d, s):
        d.rounded_rectangle((6 * s, 6 * s, 294 * s, 294 * s), radius=44 * s,
                            fill=(255, 255, 255, 14), outline=GOLD + (255,), width=8 * s)

    img = supersampled(size, size, draw)
    p = text_sprite("P", "display_bold", 210, GOLD_LIGHT)
    img.alpha_composite(p, ((size - p.width) // 2, (size - p.height) // 2 - 6))
    return img


def clock_sprite(t):
    size = 180

    def draw(d, s):
        c = size * s / 2
        r = 80 * s
        d.ellipse((c - r, c - r, c + r, c + r), outline=GOLD + (255,), width=5 * s)
        for i in range(12):
            a = i / 12 * 2 * math.pi
            r1, r2 = 66 * s, 74 * s
            d.line([(c + r1 * math.sin(a), c - r1 * math.cos(a)), (c + r2 * math.sin(a), c - r2 * math.cos(a))],
                   fill=GOLD + (200,), width=3 * s)
        am = t * 2.2
        ah = t * 0.35
        d.line([(c, c), (c + 56 * s * math.sin(am), c - 56 * s * math.cos(am))], fill=WHITE + (255,), width=4 * s)
        d.line([(c, c), (c + 36 * s * math.sin(ah), c - 36 * s * math.cos(ah))], fill=GOLD_LIGHT + (255,), width=6 * s)
        rr = 7 * s
        d.ellipse((c - rr, c - rr, c + rr, c + rr), fill=GOLD_LIGHT + (255,))

    return supersampled(size, size, draw)


# --------------------------------------------------------------------------
# Hintergrund
# --------------------------------------------------------------------------
@lru_cache(maxsize=None)
def base_background():
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    grad = BG_TOP * (1 - y) + BG_BOT * y
    grad = np.repeat(grad, W, axis=1)
    xx, yy = np.meshgrid(np.linspace(-1, 1, W), np.linspace(-1, 1, H))
    vig = 1 - 0.35 * np.clip((xx ** 2 * 0.8 + yy ** 2) - 0.25, 0, 1)
    img = (grad * vig[:, :, None]).clip(0, 255).astype(np.uint8)
    return Image.fromarray(img, "RGB").convert("RGBA")


@lru_cache(maxsize=None)
def glow_sprite(size, color, max_a):
    xx, yy = np.meshgrid(np.linspace(-1, 1, size), np.linspace(-1, 1, size))
    d = np.sqrt(xx ** 2 + yy ** 2)
    a = np.clip(1 - d, 0, 1) ** 2.2 * max_a
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = a.astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


@lru_cache(maxsize=None)
def dark_overlay():
    """Abdunklung über Fotos, damit Text lesbar bleibt."""
    y = np.linspace(0, 1, H)[:, None]
    a = (150 + 70 * np.abs(y - 0.5) * 2).repeat(W, axis=1)
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = 8, 13, 26
    arr[..., 3] = a.astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


PARTICLES = np.random.default_rng(42).random((46, 4))


def draw_background(frame, t):
    for i, (cx, cy, r, col, a) in enumerate([
        (0.22, 0.30, 1100, GOLD, 34),
        (0.80, 0.72, 1300, (60, 90, 160), 40),
        (0.62, 0.18, 900, GOLD_LIGHT, 18),
    ]):
        x = W * cx + 140 * math.sin(t * 0.17 + i * 2.1)
        y = H * cy + 90 * math.cos(t * 0.13 + i * 1.3)
        blit(frame, glow_sprite(r, col, a), x, y)
    for px, py, ps, ph in PARTICLES:
        y = (py * (H + 80) - t * (12 + 22 * ps)) % (H + 80) - 40
        x = px * W + 18 * math.sin(t * 0.4 + ph * 6.28)
        a = 0.15 + 0.35 * (0.5 + 0.5 * math.sin(t * 1.3 + ph * 6.28))
        blit(frame, dot_sprite(1.2 + 2.2 * ps, GOLD_LIGHT), x, y, alpha=a)


def find_photo(key):
    if not os.path.isdir(PHOTO_DIR):
        return None
    for ext in ("jpg", "jpeg", "png", "webp"):
        hits = sorted(glob.glob(os.path.join(PHOTO_DIR, f"{key}*.{ext}")))
        if hits:
            return hits[0]
    return None


@lru_cache(maxsize=16)
def photo_cover(path):
    img = Image.open(path).convert("RGB")
    tw, th = int(W * 1.12), int(H * 1.12)
    s = max(tw / img.width, th / img.height)
    img = img.resize((int(img.width * s + 0.5), int(img.height * s + 0.5)), Image.LANCZOS)
    l, t = (img.width - tw) // 2, (img.height - th) // 2
    return img.crop((l, t, l + tw, t + th))


def draw_photo(frame, key, tl, dur, alpha):
    path = find_photo(key)
    if not path or alpha <= 0.004:
        return
    img = photo_cover(path)
    z = 1.0 - 0.10 * (tl / dur)  # langsamer Zoom hinein
    cw, ch = img.width * z, img.height * z
    l = (img.width - cw) / 2 + 30 * math.sin(tl * 0.2)
    t = (img.height - ch) / 2
    crop = img.resize((W, H), Image.BILINEAR, box=(l, t, l + cw, t + ch)).convert("RGBA")
    crop.alpha_composite(dark_overlay())
    crop.putalpha(int(255 * alpha))
    frame.alpha_composite(crop)


# --------------------------------------------------------------------------
# Szenen
# --------------------------------------------------------------------------
def fill_rect(frame, x0, y0, x1, y1, color, alpha):
    """Halbtransparentes Rechteck korrekt einblenden (ImageDraw mischt auf RGBA nicht)."""
    x0, y0 = max(0, int(round(x0))), max(0, int(round(y0)))
    x1, y1 = min(W, int(round(x1))), min(H, int(round(y1)))
    a = int(255 * clamp(alpha))
    if x1 <= x0 or y1 <= y0 or a <= 0:
        return
    frame.alpha_composite(Image.new("RGBA", (x1 - x0, y1 - y0), color + (a,)), (x0, y0))


def gold_line(frame, cx, y, half_w, alpha, thickness=2):
    fill_rect(frame, cx - half_w, y, cx + half_w, y + thickness, GOLD, alpha)


def heading(frame, text, t, x, y, start=0.2, size=84, anchor="c", so=1.0, color=WHITE):
    p = prog(t, start, 0.8)
    blit(frame, text_sprite(text, "serif", size, color), x, y + 30 * (1 - p), alpha=p * so, anchor=anchor)


def scene_intro(frame, t, dur):
    so = out_fade(t, dur)
    p = prog(t, 0.3, 1.0)
    blit(frame, crown_sprite(), W / 2, 300 + 20 * (1 - p), alpha=p * so, scale=0.85 + 0.15 * p)
    p = prog(t, 0.9, 0.9)
    blit(frame, text_sprite(C.NAME.upper(), "serif", 140, WHITE, tracking=6), W / 2, 480 + 30 * (1 - p), alpha=p * so)
    p = prog(t, 1.2, 1.2)
    gold_line(frame, W / 2, 575, 560 * p, so)
    p = prog(t, 1.5, 0.9)
    blit(frame, text_sprite(C.CITY.upper(), "sans_light", 40, GOLD_LIGHT, tracking=26), W / 2, 630, alpha=p * so)
    p = prog(t, 2.4, 1.0)
    blit(frame, text_sprite(C.TAGLINE, "serif_italic", 56, MUTED), W / 2, 760 + 20 * (1 - p), alpha=p * so)


def scene_lage(frame, t, dur):
    so = out_fade(t, dur)
    x0 = 170
    heading(frame, "Mitten in Mettmann", t, x0, 330, start=0.15, size=100, anchor="l", so=so)
    p = prog(t, 0.6, 0.9)
    fill_rect(frame, x0 + 8, 410, x0 + 8 + 180 * p, 413, GOLD, so)
    rows = [
        (C.ADDRESS_STREET, "sans_medium", 48, WHITE, 500),
        (C.ADDRESS_CITY, "sans_medium", 48, WHITE, 566),
        ("Direkt in der Mettmanner Innenstadt", "sans_light", 36, MUTED, 660),
        ("Einkaufen · Genießen · Erledigen", "sans_light", 36, GOLD_LIGHT, 712),
    ]
    for i, (txt, key, size, col, y) in enumerate(rows):
        p = prog(t, 0.9 + i * 0.25, 0.8)
        blit(frame, text_sprite(txt, key, size, col), x0 + 40 * (1 - p), y, alpha=p * so, anchor="l")

    # stilisierte Karte (abstrakt, nicht maßstäblich)
    px, py, pw, ph = 1080, 200, 680, 680
    p = prog(t, 0.4, 1.0)
    blit(frame, panel_sprite(pw, ph, 28, 12, 90), px + pw / 2, py + ph / 2 + 30 * (1 - p), alpha=p * so)
    grid_p = prog(t, 0.8, 2.2)
    a = 0.16 * so * p
    for i in range(1, 7):
        gx = px + i * pw / 7
        fill_rect(frame, gx, py + 30, gx + 1, py + 30 + (ph - 60) * grid_p, (200, 210, 230), a)
        gy = py + i * ph / 7
        fill_rect(frame, px + 30, gy, px + 30 + (pw - 60) * grid_p, gy + 1, (200, 210, 230), a)
    # Hauptstraße
    sp = prog(t, 1.4, 1.4)
    my = py + ph * 0.58
    fill_rect(frame, px + 30, my - 6, px + 30 + (pw - 60) * sp, my + 6, GOLD, 0.75 * so)
    pl = prog(t, 2.2, 0.8)
    blit(frame, label_pill("Talstraße", "sans_medium", 28, GOLD_LIGHT), px + 56, my + 40, alpha=pl * so, anchor="l")
    # Pin fällt herab + Wellen
    pin_t = t - 2.0
    if pin_t > 0:
        drop = ease_out(pin_t / 0.7)
        bounce = math.exp(-pin_t * 5) * math.sin(pin_t * 18) * 10 if pin_t > 0.7 else 0
        cx = px + pw / 2
        tip_y = my - 2
        for k in range(3):
            rt = ((pin_t - 0.6 - k * 0.6) % 1.8) / 1.8 if pin_t > 0.6 + k * 0.6 else None
            if rt is not None:
                r = int(20 + 130 * rt)
                blit(frame, dot_sprite(r, GOLD, ring=3), cx, tip_y, alpha=(1 - rt) * 0.8 * so)
        blit(frame, pin_sprite(), cx, tip_y - 62 - 260 * (1 - drop) + bounce, alpha=min(1, pin_t * 3) * so)
        lp = prog(t, 3.0, 0.8)
        blit(frame, label_pill(C.NAME, "serif", 40, WHITE), cx, tip_y - 175, alpha=lp * so)


def fmt_de(n):
    return f"{n:,}".replace(",", ".")


def scene_zahlen(frame, t, dur):
    so = out_fade(t, dur)
    heading(frame, "Die Galerie in Zahlen", t, W / 2, 230, start=0.15, size=88, so=so)
    cols = [W / 2 - 560, W / 2, W / 2 + 560]
    for i, (value, prefix, suffix, label, sub) in enumerate(C.STATS):
        st = 0.7 + i * 0.45
        p = prog(t, st, 0.8)
        cnt = ease_out((t - st) / 2.0)
        num = prefix + fmt_de(int(round(value * cnt))) + suffix
        spr = fit_text(num, "display_bold", 150, GOLD_LIGHT, 500)
        blit(frame, spr, cols[i], 520 + 30 * (1 - p), alpha=p * so)
        blit(frame, text_sprite(label, "sans_semibold", 40, WHITE), cols[i], 655, alpha=p * so)
        blit(frame, text_sprite(sub, "sans_light", 30, MUTED), cols[i], 710, alpha=p * so)
        if i > 0:
            lp = prog(t, st, 1.0)
            x = (cols[i - 1] + cols[i]) / 2
            fill_rect(frame, x, 600 - 170 * lp, x + 2, 600 + 170 * lp, GOLD, 0.5 * so)
    p = prog(t, 3.2, 0.9)
    blit(frame, text_sprite(C.STATS_NOTE, "sans_light", 26, MUTED), W / 2, 930, alpha=p * so * 0.9)


def scene_geschichte(frame, t, dur):
    so = out_fade(t, dur)
    heading(frame, "Ein Ort im Wandel", t, W / 2, 200, start=0.15, size=88, so=so)
    x_l, x_r, y = 260, W - 260, 540
    lp = ease_in_out((t - 0.6) / 4.4)
    fill_rect(frame, x_l, y - 1, x_l + (x_r - x_l) * lp, y + 2, GOLD, 0.7 * so)
    xs = [360, W / 2, W - 360]
    for i, (year, title, sub) in enumerate(C.TIMELINE):
        st = 0.9 + i * 1.6
        p = prog(t, st, 0.8)
        if p <= 0:
            continue
        x = xs[i]
        pulse = 1 + 0.25 * math.exp(-(t - st) * 3) * math.sin((t - st) * 10)
        blit(frame, dot_sprite(26, GOLD, ring=3), x, y, alpha=p * so * 0.8, scale=pulse)
        blit(frame, dot_sprite(13, GOLD_LIGHT), x, y, alpha=p * so)
        blit(frame, text_sprite(year, "serif_bold", 76, GOLD_LIGHT), x, y - 110 + 20 * (1 - p), alpha=p * so)
        blit(frame, fit_text(title, "sans_semibold", 36, WHITE, 500), x, y + 90 - 15 * (1 - p), alpha=p * so)
        blit(frame, fit_text(sub, "sans_light", 28, MUTED, 500), x, y + 140 - 15 * (1 - p), alpha=p * so)
    for i, txt in enumerate(C.RELAUNCH_FACTS):
        p = prog(t, 6.2 + i * 0.35, 0.8)
        spr = text_sprite(txt, "sans_medium", 32, WHITE)
        pw = spr.width + 70
        x = W / 2 + (-1 if i == 0 else 1) * (pw / 2 + 20)
        blit(frame, panel_sprite(int(pw), 76, 38, 18, 160), x, 860 + 20 * (1 - p), alpha=p * so)
        blit(frame, spr, x, 860 + 20 * (1 - p), alpha=p * so)


def scene_shops(frame, t, dur):
    so = out_fade(t, dur)
    heading(frame, "Vielfalt unter einem Dach", t, W / 2, 165, start=0.15, size=88, so=so)
    p = prog(t, 0.5, 0.8)
    blit(frame, text_sprite("Mode · Drogerie · Bücher · Gastronomie · Services", "sans_light", 34, GOLD_LIGHT),
         W / 2, 250, alpha=p * so)
    tw, th, gap = 300, 190, 30
    x_start = (W - (5 * tw + 4 * gap)) / 2 + tw / 2
    for i, (cat, name) in enumerate(C.SHOPS):
        r, c = divmod(i, 5)
        x = x_start + c * (tw + gap)
        y = 480 + r * (th + gap)
        st = 0.9 + i * 0.16
        p = prog(t, st, 0.7)
        if p <= 0:
            continue
        yy = y + 40 * (1 - p)
        blit(frame, panel_sprite(tw, th), x, yy, alpha=p * so)
        blit(frame, text_sprite(cat.upper(), "sans_semibold", 20, GOLD, tracking=3), x - tw / 2 + 22, yy - 58,
             alpha=p * so, anchor="l")
        lines = name.split("\n")
        for j, ln in enumerate(lines):
            off = (j - (len(lines) - 1) / 2) * 44
            blit(frame, fit_text(ln, "serif", 46, WHITE, tw - 40), x, yy + 22 + off, alpha=p * so)
    p = prog(t, 3.5, 0.9)
    blit(frame, text_sprite(C.SHOPS_NOTE, "sans_light", 24, MUTED), W / 2, 1000, alpha=p * so * 0.9)


def scene_parken(frame, t, dur):
    so = out_fade(t, dur)
    p = prog(t, 0.2, 0.9)
    pulse = 1 + 0.015 * math.sin(t * 2.6)
    blit(frame, parking_sprite(), 450, 540 + 30 * (1 - p), alpha=p * so, scale=(0.9 + 0.1 * p) * pulse)
    heading(frame, "Bequem ankommen", t, 760, 300, start=0.3, size=96, anchor="l", so=so)
    for i, txt in enumerate(C.PARKING):
        st = 0.9 + i * 0.45
        p = prog(t, st, 0.7)
        y = 450 + i * 105
        blit(frame, check_sprite(), 790, y, alpha=p * so, scale=0.7 + 0.3 * p)
        blit(frame, text_sprite(txt, "sans_medium", 42, WHITE), 850 + 30 * (1 - p), y, alpha=p * so, anchor="l")


def scene_zeiten(frame, t, dur):
    so = out_fade(t, dur)
    p = prog(t, 0.1, 0.8)
    blit(frame, clock_sprite(t), W / 2, 270, alpha=p * so, scale=0.85 + 0.15 * p)
    heading(frame, "Öffnungszeiten", t, W / 2, 440, start=0.3, size=88, so=so)
    p = prog(t, 0.8, 0.8)
    blit(frame, text_sprite(C.HOURS_DAYS, "sans_medium", 52, WHITE), W / 2, 560 + 20 * (1 - p), alpha=p * so)
    p = prog(t, 1.2, 0.9)
    blit(frame, text_sprite(C.HOURS_TIME, "display_bold", 132, GOLD_LIGHT), W / 2, 690, alpha=p * so,
         scale=0.92 + 0.08 * p)
    p = prog(t, 1.9, 0.8)
    blit(frame, text_sprite(C.HOURS_NOTE, "sans_light", 30, MUTED), W / 2, 830, alpha=p * so)


def scene_outro(frame, t, dur):
    p = prog(t, 0.1, 0.9)
    blit(frame, crown_sprite(), W / 2, 280, alpha=p, scale=0.75 + 0.1 * p)
    p = prog(t, 0.3, 0.9)
    blit(frame, text_sprite(C.NAME, "serif", 130, WHITE), W / 2, 450 + 25 * (1 - p), alpha=p)
    gold_line(frame, W / 2, 540, 360 * prog(t, 0.6, 1.0), 1.0)
    p = prog(t, 0.8, 0.8)
    blit(frame, text_sprite(f"{C.ADDRESS_STREET} · {C.ADDRESS_CITY}", "sans_medium", 42, WHITE), W / 2, 600, alpha=p)
    p = prog(t, 1.1, 0.8)
    blit(frame, text_sprite(C.WEBSITE, "sans_semibold", 46, GOLD_LIGHT, tracking=1), W / 2, 670, alpha=p)
    p = prog(t, 1.6, 1.0)
    blit(frame, text_sprite(C.CLOSING, "serif_italic", 58, MUTED), W / 2, 800 + 20 * (1 - p), alpha=p)


# (Schlüssel, Start, Ende, Funktion) – Grenzen liegen auf Musiktakten (2,5 s)
SCENES = [
    ("intro", 0.0, 7.5, scene_intro),
    ("lage", 7.5, 15.0, scene_lage),
    ("zahlen", 15.0, 22.5, scene_zahlen),
    ("geschichte", 22.5, 32.5, scene_geschichte),
    ("shops", 32.5, 42.5, scene_shops),
    ("parken", 42.5, 50.0, scene_parken),
    ("zeiten", 50.0, 55.0, scene_zeiten),
    ("outro", 55.0, 60.0, scene_outro),
]


def corner_mark(frame, t):
    a = ease_in_out((t - 7.6) / 0.8) * ease_in_out((54.8 - t) / 0.6)
    if a <= 0:
        return
    blit(frame, crown_sprite(0.18), 92, 70, alpha=a * 0.9)
    blit(frame, text_sprite(C.NAME.upper(), "sans_semibold", 20, GOLD_LIGHT, tracking=5), 130, 70, alpha=a * 0.85,
         anchor="l")
    # Fortschrittslinie unten
    fill_rect(frame, 0, H - 4, W * (t / DURATION), H, GOLD, 0.6 * a)


def render_frame(i):
    t = i / FPS
    frame = base_background().copy()
    draw_background(frame, t)
    for key, s, e, fn in SCENES:
        if s - 0.6 <= t < e + 0.6:
            tl, dur = t - s, e - s
            # Foto-Hintergrund überblendet weich zwischen den Szenen
            pa = ease_in_out((tl + 0.5) / 1.0) * ease_in_out((dur - tl + 0.5) / 1.0)
            draw_photo(frame, key, max(0.0, tl), dur, pa)
    for key, s, e, fn in SCENES:
        if s <= t < e:
            fn(frame, t - s, e - s)
    corner_mark(frame, t)
    arr = np.asarray(frame.convert("RGB"), dtype=np.float32)
    fade = ease_in_out(t / 0.6) * ease_in_out((DURATION - t) / 1.2)
    if fade < 0.999:
        arr *= fade
    return arr.astype(np.uint8).tobytes()


def preview(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    times = [3.5, 11.5, 20.0, 30.5, 39.5, 47.5, 53.0, 58.0]
    thumbs = []
    for k, t in enumerate(times):
        img = Image.frombytes("RGB", (W, H), render_frame(int(t * FPS)))
        img.save(os.path.join(out_dir, f"preview_{k + 1:02d}_{SCENES[k][0]}.png"))
        thumbs.append(img.resize((W // 4, H // 4), Image.LANCZOS))
    sheet = Image.new("RGB", (W // 2, (H // 4) * 4), (0, 0, 0))
    for k, th in enumerate(thumbs):
        sheet.paste(th, ((k % 2) * (W // 4), (k // 2) * (H // 4)))
    sheet.save(os.path.join(out_dir, "kontaktbogen.png"))
    print("Vorschau gespeichert in", out_dir)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true", help="nur Standbilder rendern")
    ap.add_argument("--out", default=os.path.join(OUT_DIR, "galerie-koenigshof-mettmann-60s.mp4"))
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    args = ap.parse_args()

    if args.preview:
        preview(os.path.join(OUT_DIR, "preview"))
        return

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    import music
    wav = os.path.join(os.path.dirname(args.out), "music.wav")
    print("Erzeuge Musik …")
    music.render(wav, DURATION)

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", wav,
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", "-shortest",
        "-metadata", f"title={C.NAME} {C.CITY} – Präsentation",
        args.out,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    print(f"Rendere {NFRAMES} Frames mit {args.workers} Prozessen …")
    with Pool(args.workers) as pool:
        for n, buf in enumerate(pool.imap(render_frame, range(NFRAMES), chunksize=6)):
            proc.stdin.write(buf)
            if n % 150 == 0:
                print(f"  {n / FPS:5.1f} s", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        sys.exit("ffmpeg fehlgeschlagen")
    os.remove(wav)
    print("Fertig:", args.out)


if __name__ == "__main__":
    main()
