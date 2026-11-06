"""Rendert Vorschaubilder der WarAZ-Vorlagen nach assets/ww1/templates/ (Intro, Overlays, Endcard).

  python3 -m warazlib.template_previews <hintergrund.jpg>
"""
import os
import sys

import numpy as np
from PIL import Image

from . import ui as UI, cards as CD

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "ww1", "templates")


def _bg(path, dim=1.0):
    im = Image.open(path).convert("RGB").resize((1920, 1080))
    return np.asarray(im).astype(np.float32) * dim


def _save(frame, ov, name):
    fr = UI.composite(frame, ov.rgba())
    Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8)).save(os.path.join(OUT, name), quality=90)
    print(name)


def main(bg):
    os.makedirs(OUT, exist_ok=True)
    # Intro-Titel
    ov = UI.Overlay()
    CD.title(ov, 1.0, 0.0, big="VERDUN", year="1916", sub="302 TAGE AN DER MAAS")
    _save(_bg(bg, 0.45), ov, "intro_title.jpg")
    # Overlay-Satz (Zähler, Ortslabel, Datumstitel, Zahl-Karte, Lower Third, KI-Tag)
    ov = UI.Overlay()
    ov.counter("21. FEBRUAR 1916", 1, 1.0)
    ov.place("FORT DOUAUMONT", 1250, 300, 1.0, side=1, sub="FORT")
    ov.date_title("21. FEBRUAR 1916", "07:15 UHR", 1.0)
    ov.number_card("1.200+", "GESCHÜTZE", 1.0, x=1340, y=760)
    CD.lower_third(ov, 1.0, "ERICH VON FALKENHAYN", "CHEF DER OHL")
    CD.ai_tag(ov, 1.0)
    _save(_bg(bg), ov, "overlays.jpg")
    # Kapitel + Zitat
    ov = UI.Overlay()
    ov.chapter(4, "DIE HEILIGE STRASSE", 1.0)
    _save(_bg(bg, 0.8), ov, "chapter.jpg")
    ov = UI.Overlay()
    ov.quote("Courage ! On les aura !", "Philippe Pétain, Tagesbefehl vom 10. April 1916 · „Mut! Wir kriegen sie!“", 1.0)
    _save(_bg(bg, 0.8), ov, "quote.jpg")
    # Frage / Teaser / Endcard
    ov = UI.Overlay()
    CD.question(ov, 1.0, "WARUM STARBEN HIER ~300.000\nMENSCHEN FÜR EIN PAAR KILOMETER?")
    _save(_bg(bg, 0.6), ov, "question.jpg")
    ov = UI.Overlay()
    CD.teaser(ov, 1.0, 0.0)
    _save(_bg(bg, 0.6), ov, "teaser.jpg")
    ov = UI.Overlay()
    CD.endcard(ov, 1.0, 0.0)
    _save(_bg(bg), ov, "endcard.jpg")


if __name__ == "__main__":
    main(sys.argv[1])
