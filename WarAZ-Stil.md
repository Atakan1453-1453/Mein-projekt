# WarAZ – Stilhandbuch

Gilt für alle WarAZ-Videos: Kriege und Militärgeschichte, deutsch. Referenzprojekt: **Verdun 1916** (`projects/verdun_1916/`).
Kanalname gesprochen: **„War A Zett“**.

---

## 1. Format „Die lebendige Karte“

- **Langvideo:** 10–14 min, 16:9, 1920×1080, 30 fps, H.264 (crf 17) + AAC 320k, −14 LUFS / True Peak −1,5 dB.
- **Shorts:** 9:16, 1080×1920, 30–60 s.
- **Bildsprache:** animierte 2,5D-Strategiespiel-Karte mit echtem Relief (Höhenmodell), Flüssen, Wäldern, Feldern, Dörfern und Forts.
  - Die Kamera ist **immer** in Bewegung (Drift, Schwenk, Zoom). Kein Standbild länger als 5 s.
  - **Brettspiel-Figuren** auf runden Sockeln: Deutsche feldgrau, Franzosen horizontblau.
  - Weitere Nationen: Briten khaki, Osmanen oliv, Russen erdgrün, Österreich-Ungarn hechtgrau.
- **Die Karte verändert sich mit der Zeit:**
  - Wälder werden zu Stümpfen, Kraterfelder breiten sich entlang der Frontlinie aus.
  - Dörfer werden Ruinen, Forts bekommen Ruinen-Sprites.
  - Jahreszeiten: Schnee, Sommer, Herbst. Tageszeiten: Nacht und Dämmerung.
- **Effekte:**
  - Explosionen sind Flipbooks; Mündungsfeuer, Rauch, Feuer und Krater kommen dazu.
  - Gas als gelbgrüne Wolke; Wetter: Schneefall, Regen, Nebel.
- **KI-Szenen:**
  - Pro Video 2–4 kurze Szenen (4 s), in denen die Kamera „in die Karte eintaucht“.
  - Immer mit dem Tag **„KI-REKONSTRUKTION“** unten rechts.
  - Zuerst als 480p-Entwürfe erzeugen, nur gute auf 1080p hochskalieren.
- **Etwas Neues alle 5–8 s:** ein Label, eine Figur, eine Zahl, ein Kameraziel oder ein Effekt.

## 2. Farben und Schrift

| Rolle | Farbe (RGB) |
|---|---|
| Text | 238, 233, 224 |
| gedämpft | 176, 172, 164 |
| Plakette (Hintergrund) | 14, 16, 20 · Alpha 200 |
| Akzent / Signalrot | 200, 56, 38 |
| Warnung / „umstritten“ / „Schätzung“ | 232, 184, 52 |
| Deutsche (feldgrau) | 132, 136, 122 |
| Franzosen (horizontblau) | 104, 138, 186 |

- **Schrift:** Barlow Condensed (ExtraBold für Titel, Bold/SemiBold für Labels) und Barlow Medium für Fließtext.
  Die Dateien liegen in `assets/fonts/` (SIL Open Font License).
- **Plaketten:** kantig, mit schräg abgeschnittener Ecke und rotem Akzentbalken links. Keine runden Sprechblasen.
- **Großbuchstaben** mit leichter Sperrung für Orte, Daten und Kapitel.

## 3. Einblendungen (Vorlagen)

Code: `warazlib/ui.py` (Overlay) und `warazlib/cards.py`.
Vorschaubilder: `assets/ww1/templates/` (neu erzeugen mit `python3 -m warazlib.template_previews <bild.jpg>`).

| Element | Funktion | Vorschau |
|---|---|---|
| Intro-Titel | `cards.title(ov, k, t, big, year, sub)` | `intro_title.jpg` |
| Zähler unten links (Datum + „TAG X“) | `ov.counter(datum, tag, alpha)` | `overlays.jpg` |
| Ortslabel mit Rautenmarker | `ov.place(text, x, y, p, side, sub)` | `overlays.jpg` |
| Datumstitel Mitte | `ov.date_title(gross, klein, p)` | `overlays.jpg` |
| Zahl-Karte | `ov.number_card(zahl, label, p)` | `overlays.jpg` |
| Namens-Einblender | `cards.lower_third(ov, k, name, rolle)` | `overlays.jpg` |
| KI-Kennzeichnung | `cards.ai_tag(ov, k)` | `overlays.jpg` |
| Kapitelkarte | `ov.chapter(nr, titel, p)` | `chapter.jpg` |
| Zitat (immer mit Quelle + Datum) | `ov.quote(text, quelle, p, badge)` | `quote.jpg` |
| Leitfrage / Antwort | `cards.question()` / `cards.answer()` | `question.jpg` |
| Teaser nächstes Video | `cards.teaser(ov, k, t, …)` | `teaser.jpg` |
| Endcard (Abo + 2 Felder für Endbildschirm) | `cards.endcard(ov, k, t)` | `endcard.jpg` |
| Infografiken | `clock14`, `metronome`, `city`, `scales`, `wheel`, `document`, `bar`, `tick_counter`, `medallion`, `stamp`, `headline` | – |

- Der Zähler trägt die Überschrift „SCHLACHT UM VERDUN“ in `ui.Overlay.counter`. Bei neuen Videos diesen Text anpassen.
- Der **Zähler** läuft unauffällig mit und verschwindet während der KI-Szenen.
- **Umstrittenes** bekommt eine gelbe Plakette („WORTLAUT UMSTRITTEN“, „SCHÄTZUNG“).

## 4. Sprecher

- **Stimme:** ElevenLabs v4, Preset **Alistair**, `voice_id = d9d5c263-f84e-4752-97b5-3750fcc6fd2f`.
  - Festgelegt in `config/voice.txt` und dieselbe Stimme wie bei Çanakkale/Gallipoli und Verdun.
  - Higgsfield: `generate_audio(model="elevenlabs_v4", dialogue=[{text, voice_type:"preset", voice_id}])`.
- **Absatzweise generieren:** ein Absatz pro Auftrag, höchstens 7 Aufträge pro Batch, sonst gibt es HTTP 429.
- **Nachbearbeitung:**
  - Stille am Anfang und Ende abschneiden; Pausen über 0,5 s auf 0,42 s kürzen.
  - Danach `atempo=1.06`.
- **Ton:** tief, ruhig, dramatisch-dokumentarisch. Kurze Sätze.
- **Zahlen greifbar machen:** Vergleiche statt nackter Zahlen, z. B. „so viele Menschen, wie in Karlsruhe leben“ oder „alle 14 Sekunden ein Lastwagen“.
- **Französische (und andere fremde) Namen** im TTS-Text lautschriftlich schreiben. Die Liste steht in `projects/verdun_1916/script_data.py` → `PRONUNCIATION`.
  - Beispiele: Wer-döng (Verdun), Du-o-mong (Douaumont), Pe-täng (Pétain), Woh (Vaux), Woa Sa-kreh (Voie Sacrée), Luw-mong (Louvemont), War A Zett (WarAZ).
  - In Untertiteln und Einblendungen steht immer die **richtige** Schreibweise.
- **Zahlen und Jahreszahlen** im TTS-Text ausschreiben („neunzehnhundertsechzehn“).
- **Inhaltliche Regeln:**
  - Keine erfundenen Zitate. Echte Zitate nur mit Quelle und Datum, im Bild als Zitat-Karte.
  - Ein trockener Kommentar über die Führung ist erlaubt. **Nie** Witze über Soldaten oder Opfer.
  - Soldatenperspektive nur mit belegtem Feldpostbrief oder als namenlose Figur „ein Soldat wie viele“, ohne wörtliche Rede.

## 5. Dramaturgie (Pflicht)

1. **Hook-Frage** in den ersten 30 s. Sie wird erst im Finale beantwortet (Verdun: „Warum starben hier rund 300.000 Menschen für ein paar Kilometer?“).
2. **Offene Schleife** früh im Video, die später aufgelöst wird (Verdun: „Merk dir diesen Namen: Fort Douaumont“ → Kapitel 3; die verschwundene Weihnachtsdenkschrift → Finale; „Ob er von dieser Straße zurückkommt …“ → Kapitel 6).
3. **Mini-Cliffhanger** am Ende jedes Kapitels.
4. **Soldatenperspektive** (siehe oben).
5. **Struktur:**
   - Hook
   - Ausgangslage
   - Angriff
   - Wendepunkt / Logistik
   - Hölle
   - Wende
   - Finale (Antwort auf die Hook-Frage)
   - Outro mit Teaser auf das nächste Video und Abo-Bitte („Abonniere War A Zett“)
6. **Umstrittene Punkte** werden im Video als umstritten erzählt.

## 6. Recherche

- Datei: `research/sources.md` mit den Markierungen ✅ belegt · ⚠️ Zahl schwankt („rund“, „etwa“) · ❓ umstritten · ✂️ nicht belegt (wird nicht verwendet).
- Jede Zahl im Skript braucht eine Zeile in `sources.md`.
- Die Beschreibung bekommt Literatur, wichtige Links, Kartendaten-Lizenzen und einen KI-Hinweis.

## 7. Musik und Ton

- **Nur lizenzfreie Musik:** eigene Kompositionen als MIDI in `sound.py`, gerendert mit FluidSynth und dem Soundfont FluidR3_GM (MIT).
  - Für jedes Kapitel ein eigenes Motiv: Pads, Ostinato, Pauken, Hits auf Schlüsselmomente.
  - An dramatischen Stellen bricht die Musik ab (Stille vor dem Schlag).
- **Soundeffekte** synthetisch (`warazlib/audio.py`: boom, rumble, wind, place …) und nach den Ereignissen der Szene getaktet.
- **Mix:**
  - Musik wird unter der Stimme abgesenkt (Ducking).
  - Zielwerte: Stimme ca. −17,6 LUFS, Musik ca. −28 LUFS, SFX ca. −26 LUFS.
  - Gesamt: 2-pass-loudnorm auf −14 LUFS / TP −1,5.

## 8. Shorts

- Hook-Satz und Stimme ab der **ersten Sekunde**. Jeder Short bekommt eine eigene, kurze Hook-Aufnahme.
- **Titel-Plakette** oben (2 Zeilen, Barlow Condensed ExtraBold, 84 px) mit dem Kicker „VERDUN 1916“.
- **Große Untertitel:**
  - 96 px, weiß mit schwarzer Kontur, auf dunkler Plakette.
  - Häppchen von höchstens 3 Wörtern; das aktuelle Wort ist gelb.
- Fortschrittsbalken unten. Am Ende die Plakette „GANZES VIDEO AUF WarAZ“ und der gesprochene Satz „…siehst du auf War A Zett.“
- Bilder kommen aus der Langfassung (gleiche Story, Kamera 0,55–0,6× näher). KI-Clips werden im Cover-Zuschnitt verwendet.
- Code: `projects/verdun_1916/shorts.py`. Vorschau: `assets/ww1/templates/short_layout*.jpg`.

## 9. Thumbnail

- 1280×720. Als Grundbild eine KI-Szene im Stil eines Brettspiel-Dioramas (gpt_image_2_6, 1 Credit).
- Text per PIL:
  - Kicker-Plakette (Thema + Jahr), dazu 2 riesige Zeilen (weiß und gelb, 178 px, schwarze Kontur).
  - Rote Frage-Plakette.
  - Höchstens 5 Wörter insgesamt.
- Code: `projects/verdun_1916/thumbnail.py` (`make_thumb()`). Vorschau: `assets/ww1/templates/thumbnail_layout.jpg`.

## 10. Credits (Higgsfield)

- Vorher Kontostand prüfen und vor jedem großen Schritt schätzen. Ab der Obergrenze fragen (Verdun: 100 Credits einschließlich Asset-Bibliothek).
- Alles, was geht, im Code machen: Karte, Figuren-Animation, Effekte, Einblendungen, Musik, Schnitt.
- **Richtwerte (11/2026):**
  - Stimme: ca. 0,005 Credits pro Zeichen; ein Langvideo kostet ca. 40–45 Credits.
  - Bild (gpt_image_2_6): 1 Credit.
  - KI-Clip: seedance_2_0_mini 480p 4 s kostet 2 Credits, der Upscale auf 1080p 0,81 Credits.
- **Verdun 1916 hat insgesamt 84,44 Credits gekostet** (Stimme inkl. Stimmproben ca. 65,2 · Bilder 8 · KI-Clips 11,24). Die Asset-Bibliothek ist für spätere WW1-Videos wiederverwendbar.

## 11. Asset-Bibliothek (`assets/ww1/`)

| Pfad | Inhalt |
|---|---|
| `figures/` | Freigestellte Figuren, Brettspiel-Stil, PNG mit Alpha (siehe unten) |
| `figures/source/` | Original-Sheets der KI-Generierung |
| `fx/` | Explosion (48 Frames), Feuer, Blitz, Rauch, Mündungsfeuer, Krater, Gas – prozedural (`warazlib/fx.py`) |
| `maps/verdun/` | Kartentexturen L3 (Schlachtfeld, 6 m/px) und L2 (Region, 30 m/px). Jeweils base/damaged/moon/snow.jpg sowie forest/water/onset1/onset2/dem16.png und grid.json |
| `maps/europe1914/` | `world_1914.geojson` (historical-basemaps, GPL-3.0) für Inset-Karten |
| `templates/` | Vorschaubilder aller Vorlagen |
| `thumbnail_src/` | KI-Grundbilder für Thumbnails |

Die Figuren in `figures/`:

- **Infanterie:** de_inf_stand/run/kneel, fr_inf_stand/run/kneel; Gasmasken-Figuren de_gasmask, fr_gasmask
- **Artillerie:** de_howitzer, fr_gun75, ammo
- **Fahrzeuge und Luft:** fr_truck, fr_staffcar, de_plane, fr_plane, de_balloon
- **Weitere Figuren:** fr_carrier, fr_worker, pigeon
- **Bauten und Gelände:** fort, fort_ruin, village, village_ruin, ossuary, stumps, trench, wire

Fonts: `assets/fonts/`. Stimme: `config/voice.txt`.

## 12. Pipeline (Verdun als Vorlage)

```bash
cd projects/verdun_1916
python3 prep_map.py            # L3-Karte: Relief + WorldCover → Texturen (assets/ww1/maps/verdun)
python3 prep_map.py L2         # L2-Regionalkarte
python3 prep_damage.py         # Zerstörungs-Onsets aus der Frontverlauf-Historie
python3 make_doc.py            # Skript + Szenenliste (skript_szenenliste.md) aus script_data.py
python3 render_main.py stills  # Kontrollbilder
python3 render_main.py video --workers 4   # Bild → work/video_noaudio.mp4
python3 sound.py               # Musik + SFX + Stimme → work/audio/mix.wav
# Endmischung: ffmpeg mux + loudnorm → export/verdun_1916.mp4
python3 shorts.py prep && python3 shorts.py render 1   # (2, 3)
python3 thumbnail.py           # export/verdun_1916_thumbnail.jpg
```

- **Bausteine in `warazlib/`:**
  - Karte: `geo` (Raster), `terrain_data` (DEM/WorldCover), `mapstyle` (Texturen), `render25d` (2,5D-Kamera und Renderer), `mapfx` (Fronten, Pfeile, Lineale)
  - Szene: `story` (Keyframes, Objekte), `compose` (Bildzusammenbau, Kurzformat), `stage` (Figuren)
  - Gestaltung und Ton: `fx`, `ui`, `cards`, `insets`, `audio`
- **Für ein neues Video:**
  1. `script_data.py` und `vgeo.py` (Koordinaten, Fronten) neu schreiben.
  2. Karten mit neuem Grid erzeugen.
  3. `scenes.py` anpassen. Renderer, Effekte, Einblendungen und Ton bleiben.

## 13. Selbstkontrolle vor Abgabe

- Stichproben-Frames aus jedem Kapitel ansehen: Daten, Namen und Schreibweisen stimmen mit dem Text überein.
- **Stillstand-Check:** kein Fenster von 6 s ohne Bewegung (Bewegungsmessung mit 4 fps).
- **Sync:** Einsatz jedes Absatzes ±50 ms zur Timeline; Effekte sitzen auf dem gesprochenen Wort.
- **Lautheit:** −14 LUFS ±0,5; True Peak ≤ −1 dB.
- **Aussprache:** Stichprobe per Transkription (faster-whisper); Fremdnamen anhören.
- KI-Szenen sind gekennzeichnet, umstrittene Punkte markiert, Quellenliste in der Beschreibung.
