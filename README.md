# Galerie Königshof Mettmann – 60-Sekunden-Präsentationsvideo

> Weiteres Projekt in diesem Repo: [Çanakkale 1915 – 18-minütige Karten-Doku](canakkale/README.md)

**Fertiges Video:** [`output/galerie-koenigshof-mettmann-60s.mp4`](output/galerie-koenigshof-mettmann-60s.mp4)
(1920×1080, 30 fps, H.264/AAC, 60 s, ca. 8 MB)

## Ablauf des Videos

| Zeit | Szene | Inhalt |
|---|---|---|
| 0:00–0:07 | Intro | Krone, „GALERIE KÖNIGSHOF – Mettmann“, „Shopping im Herzen der Stadt“ |
| 0:07–0:15 | Lage | Talstraße 10 · 40822 Mettmann, stilisierte Karte mit Pin |
| 0:15–0:22 | Zahlen | 20+ Shops, 400+ Parkplätze, ca. 15.000 m² Mietfläche |
| 0:22–0:32 | Geschichte | 1972 Kaufhaus (später Hertie) → nach 2009 Königshof-Galerie → 7. Nov. 2019 Neustart als Galerie Königshof (14 Monate Umbau, über 10 Mio. €) |
| 0:32–0:42 | Shops | H&M, Deichmann, Takko, Ernsting's family, dm, easyApotheke, Thalia, Ambiente, kkiosk, Asia Friends |
| 0:42–0:50 | Parken | über 400 Plätze, schrankenlos, Bezahlung am Automaten oder per App, 24 h geöffnet |
| 0:50–0:55 | Öffnungszeiten | Mo–Sa 10:00–19:00 Uhr (Kernöffnungszeiten) |
| 0:55–1:00 | Outro | Adresse, galeriekoenigshof.de, „Wir freuen uns auf Ihren Besuch!“ |

Die Musik wird im Skript selbst synthetisiert (`video/music.py`), es gibt also keine Rechte Dritter daran.
Die Szenenwechsel liegen auf den Taktgrenzen (96 BPM, 2,5 s pro Takt).

## Neu rendern

Voraussetzungen: Python 3 mit `numpy` und `Pillow` sowie `ffmpeg`.

```bash
python3 video/render.py --preview   # Standbilder je Szene nach output/preview/ (ca. 3 s)
python3 video/render.py             # komplettes Video (ca. 1–2 min)
```

* **Texte und Fakten ändern:** alles steht in [`video/content.py`](video/content.py).
* **Eigene Fotos einbauen:** Bilder nach `assets/photos/` legen. Der Dateiname beginnt mit dem
  Szenen-Schlüssel (`intro`, `lage`, `zahlen`, `geschichte`, `shops`, `parken`, `zeiten`, `outro`),
  z. B. `assets/photos/intro.jpg` oder `assets/photos/shops_eingang.jpg`. Die Fotos werden automatisch
  abgedunkelt und mit einem langsamen Zoom (Ken-Burns-Effekt) hinter die Texte gelegt.

## Quellen (Recherche Oktober 2026)

* Center-Website [galeriekoenigshof.de](https://galeriekoenigshof.de/) – Shop-Verzeichnis, „über 20 Shops …
  über 400 Parkplätze“, [Öffnungszeiten](https://galeriekoenigshof.de/oeffnungszeiten-2/), Parkhaus 24 h
* Stadt Mettmann – [Galerie Königshof: Wiedereröffnung nach Umbau](https://www.mettmann.de/web/galerie-koenigshof-wiedereroeffnung-nach-umbau/)
* ILG Gruppe – [Wiedereröffnung der Galerie Königshof nach Umbau](https://www.ilg-gruppe.de/wiedereroeffnung-der-galerie-koenigshof-nach-umbau/)
* Radio Neandertal – [Galerie Königshof eröffnet neu](https://www.radioneandertal.de/artikel/galerie-koenigshof-eroeffnet-neu-393408)
* Schaufenster Mettmann – [Aus der Königshof-Galerie wird die Galerie Königshof](https://www.schaufenster-mettmann.de/die-stadt/aus-der-koenigshof-galerie-wird-die-galerie-koenigshof_aid-38605331)
* Gleeds – [Projektseite Königshof-Galerie](https://es.gleeds.com/projects/koenigsgalerie-mettmann-germany/) (ca. 15.000 m² Mietfläche)
* Phoenix Development – [Königshof-Galerie Mettmann](https://www.phoenix-development.de/objekte/koenigshof-galerie-mettmann/) (Gebäude von 1972, Hertie bis 2009)

**Hinweis:** Mieterliste und Öffnungszeiten stammen teils von älteren Seitenständen. Vor einer
Veröffentlichung bitte mit dem Center-Management abgleichen. Ein genaues Eröffnungsjahr der
ursprünglichen Königshof-Galerie ließ sich nicht sicher belegen und steht deshalb nicht im Video.
