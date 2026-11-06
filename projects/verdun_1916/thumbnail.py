"""Thumbnail 1280×720: KI-Grundbild (assets/ww1/thumbnail_src) + Text per PIL (Vorlage für WarAZ)."""
import os
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
from warazlib import ui as UI  # noqa: E402


def make_thumb(base, out, big=("300.000", "TOTE"), tag="FÜR EIN PAAR KM?", kicker="VERDUN 1916"):
    im = Image.open(base).convert("RGB")
    w, h = im.size
    th = int(w * 9 / 16)
    im = im.crop((0, (h - th) // 2, w, (h - th) // 2 + th)).resize((1280, 720), Image.LANCZOS)
    im = ImageEnhance.Contrast(im).enhance(1.08)
    im = ImageEnhance.Color(im).enhance(1.08)
    # Abdunkeln links oben für Lesbarkeit
    g = Image.new("L", (1280, 720), 0)
    gd = ImageDraw.Draw(g)
    for x in range(0, 760, 4):
        a = int(170 * (1 - x / 760) ** 1.4)
        gd.rectangle((x, 0, x + 4, 720), fill=a)
    g = g.filter(ImageFilter.GaussianBlur(30))
    im = Image.composite(Image.new("RGB", im.size, (8, 8, 10)), im, g)
    d = ImageDraw.Draw(im, "RGBA")
    # Kicker
    fk = UI.font("bold", 40)
    kw = UI.text_w(kicker, fk, 6)
    d.rectangle((44, 40, 44 + kw + 36, 92), fill=(14, 16, 20, 225))
    d.rectangle((44, 40, 52, 92), fill=UI.STYLE["accent"] + (255,))
    UI.spaced(d, (66, 44), kicker, fk, UI.STYLE["text"] + (255,), 6)
    # Große Zeilen
    fb = UI.font("title", 178)
    y = 100
    for i, line in enumerate(big):
        col = (255, 255, 255) if i == 0 else (255, 214, 90)
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        sd.text((50, y + 8), line, font=fb, fill=(0, 0, 0, 200), stroke_width=10, stroke_fill=(0, 0, 0, 200))
        sh = sh.filter(ImageFilter.GaussianBlur(6))
        im.paste(sh, (0, 0), sh)
        d = ImageDraw.Draw(im, "RGBA")
        d.text((44, y), line, font=fb, fill=col, stroke_width=6, stroke_fill=(10, 10, 12))
        y += 168
    # Tag-Plakette
    ft = UI.font("title", 70)
    tw = d.textlength(tag, font=ft)
    y += 26
    d.polygon([(44, y), (44 + tw + 64, y), (44 + tw + 40, y + 92), (44, y + 92)], fill=UI.STYLE["accent"] + (245,))
    d.text((70, y + 6), tag, font=ft, fill=(255, 255, 255), stroke_width=2, stroke_fill=(90, 20, 14))
    im.save(out, quality=95)
    return out


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "export"), exist_ok=True)
    out = make_thumb(os.path.join(ROOT, "assets", "ww1", "thumbnail_src", "verdun_thumb_base.png"),
                     os.path.join(ROOT, "export", "verdun_1916_thumbnail.jpg"))
    print(out, Image.open(out).size)
