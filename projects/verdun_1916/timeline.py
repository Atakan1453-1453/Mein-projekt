"""Zeitleiste aus den echten Längen der Sprecher-Absätze (voice_durations.json).

Pausen: 0,55 s zwischen Absätzen, 1,3 s vor jedem neuen Kapitel, zusätzliche Bildzeit an
einzelnen Stellen (Titel nach P04, Zeitraffer, Antwort-Karte usw.).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import script_data as S  # noqa: E402

LEAD = 1.2                    # Vorlauf vor P01
GAP = 0.42
CHAPTER_GAP = 1.0
EXTRA_AFTER = {"P02": 0.6, "P03": 0.4, "P04": 2.8, "P15": 0.6, "P23": 0.8, "P25": 0.8, "P30": 0.6, "P34": 0.9,
               "P41": 0.6, "P46": 1.0, "P50": 1.0, "P58": 0.8, "P60": 0.8, "P61": 0.6, "P64": 0.6, "P69": 1.2,
               "P71": 1.0, "P73": 5.0}


def build():
    dur = json.load(open(os.path.join(HERE, "voice_durations.json")))
    t = LEAD
    tl = {}
    prev_ch = 1
    for p in S.P:
        if p["ch"] != prev_ch:
            t += CHAPTER_GAP
            prev_ch = p["ch"]
        d = dur[p["id"]]
        tl[p["id"]] = (round(t, 3), round(t + d, 3))
        t += d + GAP + EXTRA_AFTER.get(p["id"], 0.0)
    return tl


def chapter_starts(tl):
    out = {}
    for p in S.P:
        out.setdefault(p["ch"], tl[p["id"]][0])
    return out


if __name__ == "__main__":
    tl = build()
    end = max(b for a, b in tl.values())
    print("Ende Sprache", round(end, 1), "s =", round(end / 60, 2), "min")
    for ch, t in chapter_starts(tl).items():
        print(ch, S.CHAPTERS[ch], f"{int(t // 60)}:{int(t % 60):02d}")
