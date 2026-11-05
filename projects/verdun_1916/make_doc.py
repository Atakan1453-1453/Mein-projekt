"""Erzeugt skript_szenenliste.md aus script_data.py.

Zeiten sind Schätzungen (2,45 Wörter/s + 0,7 s Pause je Absatz). Nach der
Stimm-Generierung werden sie durch die echten Längen der Audiodateien ersetzt.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import script_data as S  # noqa: E402

WPS = 2.45
PAUSE = 0.7


def fmt(t):
    m, s = divmod(int(round(t)), 60)
    return f"{m}:{s:02d}"


def cell(s):
    return (s or "–").replace("|", "/").replace("\n", " ")


def main():
    t = 0.0
    rows = []
    ch_start = {}
    for p in S.P:
        d = len(p["tts"].split()) / WPS + PAUSE
        ch_start.setdefault(p["ch"], t)
        rows.append((t, t + d, p))
        t += d
    total = t
    words = sum(len(p["tts"].split()) for p in S.P)

    out = []
    out.append("# Verdun 1916 – Skript & Szenenliste (STOPP 1)\n")
    out.append(f"Geschätzte Länge: **{fmt(total)} min** bei {words} Wörtern "
               f"({WPS} Wörter/s). {len(S.P)} Sprecher-Absätze = {len(S.P)} einzelne Stimm-Dateien.\n")
    out.append("**Leitfrage (Hook):** Warum starben hier rund 300.000 Menschen für ein paar Kilometer? "
               "**Antwort:** erst im Finale (P65–P69).\n")
    out.append("**Offene Schleifen:** (1) „Merk dir diesen Namen: Fort Douaumont“ (P07) → aufgelöst in P20–P23. "
               "(2) Die verschwundene Weihnachtsdenkschrift (P13–P15) → aufgelöst im Finale (P65/P66). "
               "(3) „Ob er von dieser Straße zurückkommt, wissen wir noch nicht“ (P34) → aufgelöst in P54.\n")
    out.append("**Soldatenperspektive:** namenlose Figur, ausdrücklich „ein Soldat wie viele“ (P33/P34, P43–P46, "
               "P54/P55). Keine erfundenen Zitate, nur belegte, typische Erlebnisse.\n")
    out.append("**KI-Videoclips:** [KI-1] Trommelfeuer im Morgengrauen (P02) · [KI-2] Fort Douaumont im "
               "Schneetreiben (P21) · [KI-3] Lastwagenkolonne nachts auf der Heiligen Straße (P28) · "
               "[KI-4, optional] Gasangriff im Trichterfeld (P45). Alles andere ist Code-Animation auf der Karte.\n")
    out.append("**Zähler** (unten links, dauerhaft): Datum + „TAG X“. Tag 1 = 21.02.1916, Tag 302 = 18.12.1916.\n")

    out.append("\n## Kapitelübersicht\n")
    out.append("| Kapitel | Start | Mini-Cliffhanger am Ende |")
    out.append("|---|---|---|")
    cliff = {
        1: "Titel → „Genau das klären wir heute.“",
        2: "„Genau hier steckt ein Teil der Antwort.“ (verschwundenes Dokument)",
        3: "„Frankreich wankt. Und jetzt braucht es jemanden, der nicht wankt.“",
        4: "„Ob er von dieser Straße zurückkommt, wissen wir noch nicht.“",
        5: "„Ein letzter Stoß, und Verdun könnte fallen. Oder?“",
        6: "„Aber ein letzter Akt fehlt noch.“",
        7: "Antwort auf die Leitfrage, Epilog Beinhaus/1984",
        8: "Teaser Somme + Abo",
    }
    for ch, name in S.CHAPTERS.items():
        out.append(f"| {ch}. {name} | {fmt(ch_start[ch])} | {cliff[ch]} |")

    out.append("\n## Aussprache im Sprechertext\n")
    out.append("Die Stimme bekommt diese Schreibweisen, auf dem Bildschirm steht immer die korrekte Schreibweise. "
               "Ob die Bindestriche Pausen erzeugen, prüfe ich in der Stimmprobe (Stopp 2) und passe sie "
               "ggf. an (z. B. „Duomong“).\n")
    out.append("| Bildschirm | Sprechertext |")
    out.append("|---|---|")
    for k, v in S.PRONUNCIATION.items():
        out.append(f"| {k} | {v} |")

    out.append("\n## Skript (Sprechertext)\n")
    cur = None
    for a, b, p in rows:
        if p["ch"] != cur:
            cur = p["ch"]
            out.append(f"\n### {cur}. {S.CHAPTERS[cur]} (ab {fmt(a)})\n")
        out.append(f"**{p['id']}** {p['tts']}\n")

    out.append("\n## Szenenliste\n")
    out.append("Legende: DE = feldgraue Figuren, FR = horizontblaue Figuren. „[KI-n]“ = echter KI-Videoclip, "
               "sonst Code-Animation. Jede Zeile enthält mehrere sichtbare Wechsel, damit spätestens alle 5–8 s "
               "etwas Neues passiert.\n")
    out.append("| Zeit | ID | Sprechertext | Kartenaktion / Bild | Einblendung | Sound |")
    out.append("|---|---|---|---|---|---|")
    for a, b, p in rows:
        out.append(f"| {fmt(a)}–{fmt(b)} | {p['id']} | {cell(p['tts'])} | {cell(p['map'])} | "
                   f"{cell(p['ins'])} | {cell(p['snd'])} |")

    path = os.path.join(HERE, "skript_szenenliste.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(path, fmt(total), words)


if __name__ == "__main__":
    main()
