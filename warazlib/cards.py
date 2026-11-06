"""WarAZ-Vorlagen für Einblendungen (wiederverwendbar für alle Videos).

Jede Funktion zeichnet auf ein ui.Overlay; k = Sichtbarkeit 0..1, t = Zeit (für Animationen).
Intro-Titel (title), Endcard (endcard) und Teaser (teaser) sind die Kanal-Vorlagen.
"""
import math

from . import ui as UI
from .ui import STYLE, font, spaced, text_w, plate, ease, ease_out


def _a(k, v=255):
    return int(v * max(0.0, min(1.0, k)))


def question(ov, k, text, y=None):
    """Fragekarte (Leitfrage) – mehrzeilig, mittig."""
    if k <= 0:
        return
    d = ov.d
    lines = text.split("\n")
    f = font("title", 72)
    w = max(text_w(l, f, 2) for l in lines)
    H_ = 92 * len(lines) + 60
    x = (ov.W - w) / 2
    y = (ov.H - H_) / 2 - 40 if y is None else y
    plate(d, (x - 60, y - 30, x + w + 60, y + H_ - 20), k, cut=20)
    UI.spaced(d, (x - 30, y - 74), "DIE FRAGE", font("bold", 30), STYLE["accent"] + (_a(k),), 4)
    for i, l in enumerate(lines):
        kk = ease((k * 1.6) - i * 0.25)
        spaced(d, (x, y + i * 92), l, f, STYLE["text"] + (_a(kk),), 2)


def answer(ov, k, text):
    if k <= 0:
        return
    d = ov.d
    lines = text.split("\n")
    f = font("title", 64)
    w = max(text_w(l, f, 2) for l in lines)
    H_ = 82 * len(lines) + 50
    x = (ov.W - w) / 2
    y = ov.H * 0.36 - H_ / 2
    plate(d, (x - 60, y - 30, x + w + 60, y + H_ - 10), k, cut=20)
    spaced(d, (x - 30, y - 74), "DIE ANTWORT", font("bold", 30), STYLE["accent"] + (_a(k),), 4)
    for i, l in enumerate(lines):
        spaced(d, (x, y + i * 82), l, f, STYLE["text"] + (_a(ease(k * 1.5 - i * 0.2)),), 2)


def title(ov, k, t, big="VERDUN", year="1916", sub="302 TAGE AN DER MAAS"):
    """Intro-Titel (Kanal-Vorlage)."""
    if k <= 0:
        return
    d = ov.d
    fb, fy, fs = font("title", 200), font("title", 120), font("semi", 38)
    wb = text_w(big, fb, 14)
    wy = text_w(year, fy, 10)
    x = (ov.W - wb) / 2
    y = ov.H * 0.30
    sp = 14 + (1 - ease_out(k)) * 30
    spaced(d, (x, y), big, fb, STYLE["text"] + (_a(k),), sp)
    d.rectangle((x, y + 236, x + wb * ease_out(k), y + 242), fill=STYLE["accent"] + (_a(k),))
    spaced(d, ((ov.W - wy) / 2, y + 258), year, fy, STYLE["accent"] + (_a(k),), 10)
    ws = text_w(sub, fs, 8)
    spaced(d, ((ov.W - ws) / 2, y + 400), sub, fs, STYLE["muted"] + (_a(k),), 8)
    spaced(d, (ov.W - 230, ov.H - 70), "WarAZ", font("title", 44), STYLE["text"] + (_a(k, 200),), 3)


def chapter(ov, k, num, name):
    ov.chapter(num, name, k)


def stamp(ov, k, text, x, y, rot=-8, color=None, size=64, strike=False):
    """Stempel (schräg, mit Rahmen)."""
    if k <= 0:
        return
    from PIL import Image, ImageDraw
    col = color or STYLE["accent"]
    f = font("title", size)
    w = int(text_w(text, f, 3)) + 50
    h = size + 40
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    sc = 1.0 + (1 - ease_out(min(1, k * 2))) * 0.6
    a = _a(k)
    dd.rectangle((4, 4, w - 5, h - 5), outline=col + (a,), width=5)
    spaced(dd, (25, 12), text, f, col + (a,), 3)
    if strike:
        dd.line((10, h * 0.55, w - 10, h * 0.45), fill=col + (a,), width=7)
    im = im.resize((int(w * sc), int(h * sc)))
    im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    ov.img.alpha_composite(im, (int(x - im.size[0] / 2), int(y - im.size[1] / 2)))


def lower_third(ov, k, name, role):
    if k <= 0:
        return
    d = ov.d
    fn, fr = font("title", 46), font("semi", 28)
    w = max(text_w(name, fn, 2), text_w(role, fr, 3)) + 70
    x, y = 70, ov.H - 260
    bw = w * ease_out(k)
    plate(d, (x, y, x + bw, y + 104), k, cut=12)
    if k > 0.5:
        a = _a((k - 0.5) * 2)
        spaced(d, (x + 30, y + 10), name, fn, STYLE["text"] + (a,), 2)
        spaced(d, (x + 32, y + 64), role, fr, STYLE["accent"] + (a,), 3)


def headline(ov, k, text, sub=None, y=None, color=None):
    if k <= 0:
        return
    d = ov.d
    f = font("title", 84)
    w = text_w(text, f, 3)
    x = (ov.W - w) / 2
    y = ov.H * 0.14 if y is None else y
    plate(d, (x - 40, y - 16, x + w + 40, y + 112 + (44 if sub else 0)), k, cut=16)
    spaced(d, (x, y), text, f, (color or STYLE["text"]) + (_a(k),), 3)
    if sub:
        fs = font("semi", 32)
        spaced(d, ((ov.W - text_w(sub, fs, 4)) / 2, y + 108), sub, fs, STYLE["accent"] + (_a(k),), 4)


def badge(ov, k, text, x, y, color=None):
    if k > 0:
        ov.badge(text, x, y, k, color)


def ai_tag(ov, k):
    """Kennzeichnung der KI-Szenen."""
    if k <= 0:
        return
    d = ov.d
    f = font("bold", 24)
    txt = "KI-REKONSTRUKTION"
    w = text_w(txt, f, 3)
    x, y = ov.W - w - 90, ov.H - 76
    plate(d, (x - 18, y - 8, x + w + 18, y + 36), k * 0.9, cut=8, accent=False)
    spaced(d, (x, y), txt, f, STYLE["muted"] + (_a(k),), 3)


# ---------------------------------------------------------------- Infografiken
def clock14(ov, k, t, cx=None, cy=None, label="ALLE 14 SEKUNDEN EIN FAHRZEUG", count_label="≈ 6.000 PRO TAG"):
    if k <= 0:
        return
    d = ov.d
    cx = ov.W - 260 if cx is None else cx
    cy = 300 if cy is None else cy
    R = 120
    plate(d, (cx - 200, cy - 170, cx + 200, cy + 230), k, cut=16)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=STYLE["text"] + (_a(k),), width=6)
    ph = (t % 1.4) / 1.4            # 14 s, 10x beschleunigt
    for i in range(14):
        a = -math.pi / 2 + i / 14 * 2 * math.pi
        d.line((cx + math.cos(a) * (R - 16), cy + math.sin(a) * (R - 16), cx + math.cos(a) * (R - 4), cy + math.sin(a) * (R - 4)),
               fill=STYLE["muted"] + (_a(k),), width=3)
    a = -math.pi / 2 + ph * 2 * math.pi
    d.pieslice((cx - R + 10, cy - R + 10, cx + R - 10, cy + R - 10), -90, -90 + ph * 360, fill=STYLE["accent"] + (_a(k, 120),))
    d.line((cx, cy, cx + math.cos(a) * (R - 14), cy + math.sin(a) * (R - 14)), fill=STYLE["text"] + (_a(k),), width=6)
    f = font("title", 54)
    spaced(d, (cx - text_w("14 s", f, 2) / 2, cy - 34), "14 s", f, STYLE["text"] + (_a(k),), 2)
    fl = font("bold", 22)
    spaced(d, (cx - text_w(label, fl, 1.5) / 2, cy + R + 22), label, fl, STYLE["accent"] + (_a(k),), 1.5)
    fc = font("bold", 34)
    spaced(d, (cx - text_w(count_label, fc, 2) / 2, cy + R + 56), count_label, fc, STYLE["text"] + (_a(k),), 2)


def bar(ov, k, frac, label, big, x=None, y=None):
    if k <= 0:
        return
    d = ov.d
    x = ov.W - 640 if x is None else x
    y = 210 if y is None else y
    plate(d, (x, y, x + 560, y + 200), k, cut=16)
    spaced(d, (x + 30, y + 14), big, font("title", 76), STYLE["text"] + (_a(k),), 2)
    spaced(d, (x + 32, y + 104), label, font("bold", 28), STYLE["accent"] + (_a(k),), 2.5)
    bx0, by0 = x + 30, y + 150
    d.rectangle((bx0, by0, bx0 + 500, by0 + 26), outline=STYLE["text"] + (_a(k),), width=2)
    d.rectangle((bx0 + 3, by0 + 3, bx0 + 3 + 494 * frac * ease_out(k), by0 + 23), fill=(104, 138, 186, _a(k)))


def metronome(ov, k, t, big="BIS ZU 60.000.000", label="GRANATEN · SCHÄTZUNG", sub="> 2 PRO SEKUNDE"):
    if k <= 0:
        return
    d = ov.d
    x, y = ov.W - 700, 170
    plate(d, (x, y, x + 630, y + 300), k, cut=16)
    spaced(d, (x + 30, y + 14), big, font("title", 76), STYLE["text"] + (_a(k),), 2)
    spaced(d, (x + 32, y + 104), label, font("bold", 28), STYLE["warn"] + (_a(k),), 2.5)
    cx, cy, R = x + 110, y + 220, 52
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=STYLE["text"] + (_a(k),), width=4)
    a = -math.pi / 2 + (t % 1.0) * 2 * math.pi
    d.line((cx, cy, cx + math.cos(a) * (R - 8), cy + math.sin(a) * (R - 8)), fill=STYLE["accent"] + (_a(k),), width=5)
    for j in range(2):
        ph = ((t * 2.3) + j * 0.5) % 1.0
        r = 6 + 22 * ph
        d.ellipse((cx + 120 + j * 70 - r, cy - r, cx + 120 + j * 70 + r, cy + r), outline=STYLE["accent"] + (_a(k * (1 - ph)),), width=4)
    spaced(d, (cx + 250, cy - 26), sub, font("bold", 40), STYLE["text"] + (_a(k),), 2)


def tick_counter(ov, k, n, big_label="WECHSEL DES BESITZERS", x=None, y=None):
    if k <= 0:
        return
    d = ov.d
    x = ov.W - 560 if x is None else x
    y = 200 if y is None else y
    plate(d, (x, y, x + 490, y + 230), k, cut=16)
    spaced(d, (x + 30, y + 10), f"{n} ×", font("title", 110), STYLE["text"] + (_a(k),), 2)
    spaced(d, (x + 32, y + 140), big_label, font("bold", 28), STYLE["accent"] + (_a(k),), 2.5)
    for i in range(16):
        c = (104, 138, 186) if i % 2 == 0 else (150, 154, 144)
        on = i < n
        d.rectangle((x + 32 + i * 27, y + 186, x + 52 + i * 27, y + 206), fill=c + (_a(k, 255 if on else 50),))


def city(ov, k, t, big="≈ 1.000 PRO TAG", label="≈ EINWOHNER VON KARLSRUHE"):
    if k <= 0:
        return
    d = ov.d
    x, y = ov.W - 720, 160
    plate(d, (x, y, x + 650, y + 360), k, cut=16)
    spaced(d, (x + 30, y + 14), big, font("title", 76), STYLE["text"] + (_a(k),), 2)
    spaced(d, (x + 32, y + 104), label, font("bold", 28), STYLE["accent"] + (_a(k),), 2.5)
    # Skyline
    import random
    rnd = random.Random(4)
    bx = x + 34
    base = y + 330
    fill = min(1.0, k * 1.2)
    while bx < x + 610:
        w = rnd.randint(22, 46)
        h = rnd.randint(40, 150)
        d.rectangle((bx, base - h, bx + w, base), fill=(60, 62, 66, _a(k)))
        # Fenster/Punkte füllen sich
        for yy in range(base - h + 8, base - 6, 12):
            for xx in range(bx + 5, bx + w - 4, 9):
                if rnd.random() < fill * 0.85:
                    d.rectangle((xx, yy, xx + 3, yy + 4), fill=(236, 230, 214, _a(k, 200)))
        bx += w + 4
    if rnd.random() < 2:
        pass


def scales(ov, k, t, left="FRANKREICH", right="DEUTSCHLAND"):
    if k <= 0:
        return
    d = ov.d
    cx, cy = ov.W / 2, 430
    plate(d, (cx - 360, cy - 120, cx + 360, cy + 190), k, cut=16)
    sink = 30 * ease(k)
    d.line((cx, cy - 80, cx, cy + 120), fill=STYLE["text"] + (_a(k),), width=6)
    d.line((cx - 230, cy - 40 + sink * 0.2, cx + 230, cy - 40 + sink * 0.2), fill=STYLE["text"] + (_a(k),), width=6)
    for sgn, name, col in ((-1, left, (104, 138, 186)), (1, right, (150, 154, 144))):
        px = cx + sgn * 230
        py = cy + 40 + sink
        d.line((px, cy - 40 + sink * 0.2, px - 60, py), fill=STYLE["muted"] + (_a(k),), width=3)
        d.line((px, cy - 40 + sink * 0.2, px + 60, py), fill=STYLE["muted"] + (_a(k),), width=3)
        d.chord((px - 80, py - 30, px + 80, py + 40), 0, 180, fill=col + (_a(k),))
        f = font("bold", 28)
        spaced(d, (px - text_w(name, f, 2) / 2, py + 52), name, f, STYLE["text"] + (_a(k),), 2)


def wheel(ov, k, t, label="NORIA = SCHÖPFRAD"):
    if k <= 0:
        return
    d = ov.d
    cx, cy, R = ov.W - 250, 300, 118
    plate(d, (cx - 190, cy - 170, cx + 190, cy + 220), k, cut=16)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=STYLE["text"] + (_a(k),), width=6)
    for i in range(8):
        a = t * 0.9 + i / 8 * 2 * math.pi
        x1, y1 = cx + math.cos(a) * R, cy + math.sin(a) * R
        d.line((cx, cy, x1, y1), fill=STYLE["muted"] + (_a(k),), width=3)
        col = (104, 138, 186) if math.sin(a) < 0 else (150, 120, 100)
        d.rectangle((x1 - 13, y1 - 9, x1 + 13, y1 + 9), fill=col + (_a(k),))
    f = font("bold", 26)
    spaced(d, (cx - text_w(label, f, 2) / 2, cy + R + 36), label, f, STYLE["accent"] + (_a(k),), 2)


def document(ov, k, t, gone=0.0, title="DENKSCHRIFT", sub="WEIHNACHTEN 1915"):
    """Dokument-Symbol, das sich auflöst (gone 0..1)."""
    if k <= 0:
        return
    d = ov.d
    x, y, w, h = ov.W - 420, 170, 300, 380
    a = k * (1 - gone)
    d.rectangle((x + 10, y + 10, x + w + 10, y + h + 10), fill=(0, 0, 0, _a(a, 90)))
    d.rectangle((x, y, x + w, y + h), fill=(226, 216, 190, _a(a)), outline=(120, 110, 90, _a(a)), width=3)
    spaced(d, (x + 26, y + 24), title, font("title", 44), (60, 50, 40, _a(a)), 2)
    spaced(d, (x + 28, y + 80), sub, font("bold", 24), (110, 60, 40, _a(a)), 2)
    for i in range(9):
        L = 240 if i % 3 else 180
        d.rectangle((x + 28, y + 130 + i * 24, x + 28 + L, y + 138 + i * 24), fill=(120, 110, 96, _a(a, 160)))
    if gone > 0:
        import random
        rnd = random.Random(2)
        for i in range(60):
            px = x + rnd.random() * w + gone * rnd.uniform(-80, 160)
            py = y + rnd.random() * h - gone * rnd.uniform(40, 220)
            r = 2 + rnd.random() * 5
            d.ellipse((px - r, py - r, px + r, py + r), fill=(160, 150, 130, _a(k * (1 - gone) * 1.5, 160)))


def medallion(ov, k, name, role, side="de"):
    """Namens-Medaillon (ohne Foto): Initialen im Kreis + Name."""
    if k <= 0:
        return
    d = ov.d
    cx, cy, R = 200, 330, 86
    col = STYLE["de"] if side == "de" else STYLE["fr"]
    d.ellipse((cx - R - 8, cy - R - 8, cx + R + 8, cy + R + 8), fill=STYLE["plate"] + (_a(k, 220),))
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=col + (_a(k),), outline=STYLE["accent"] + (_a(k),), width=5)
    ini = "".join(w[0] for w in name.replace("von ", "").split()[:2])
    f = font("title", 80)
    spaced(d, (cx - text_w(ini, f, 2) / 2, cy - 52), ini, f, STYLE["text"] + (_a(k),), 2)
    lower_third(ov, k, name, role)


def teaser(ov, k, t, line1="NÄCHSTES VIDEO", line2="DIE SCHLACHT AN DER SOMME", line3="1. JULI 1916"):
    if k <= 0:
        return
    d = ov.d
    f1, f2, f3 = font("bold", 34), font("title", 96), font("semi", 40)
    w = max(text_w(line2, f2, 3), 600)
    x = (ov.W - w) / 2
    y = ov.H * 0.30
    plate(d, (x - 50, y - 30, x + w + 50, y + 230), k, cut=20)
    spaced(d, (x, y), line1, f1, STYLE["accent"] + (_a(k),), 5)
    spaced(d, (x, y + 46), line2, f2, STYLE["text"] + (_a(k),), 3)
    spaced(d, (x, y + 160), line3, f3, STYLE["muted"] + (_a(k),), 4)


def endcard(ov, k, t):
    """Endcard (Kanal-Vorlage): Abo-Hinweis + zwei Flächen für YouTube-Endbildschirm-Videos."""
    if k <= 0:
        return
    d = ov.d
    a = _a(k)
    d.rectangle((0, 0, ov.W, ov.H), fill=(10, 11, 14, _a(k, 170)))
    spaced(d, (120, 120), "WarAZ", font("title", 120), STYLE["text"] + (a,), 4)
    spaced(d, (124, 262), "KRIEGE & MILITÄRGESCHICHTE", font("semi", 36), STYLE["muted"] + (a,), 5)
    bx, by = 124, 360
    d.rounded_rectangle((bx, by, bx + 360, by + 84), radius=10, fill=STYLE["accent"] + (a,))
    spaced(d, (bx + 56, by + 14), "ABONNIEREN", font("title", 54), (255, 255, 255, a), 3)
    for i in range(2):
        x0 = 900 + i * 0
        y0 = 150 + i * 400
        d.rectangle((x0, y0, x0 + 860, y0 + 340), outline=(230, 226, 216, _a(k, 120)), width=3)
        lab = "NÄCHSTES VIDEO" if i == 0 else "AUCH SPANNEND"
        spaced(d, (x0 + 20, y0 - 44), lab, font("bold", 30), STYLE["muted"] + (a,), 3)
