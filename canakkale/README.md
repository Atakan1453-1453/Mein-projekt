# Çanakkale 1915 – Die Schlacht um die Dardanellen (Doku, 18 Minuten)

Animierte Karten-Dokumentation auf Deutsch über den Dardanellen-Feldzug 1915/16. Das Video zeigt
den Beginn, den Verlauf und das Ende der Kämpfe auf echten Satellitenbildern. Die Kamera beginnt
mit einer Luftaufnahme über Çanakkale und fliegt zu jedem Ereignis. Truppen sind als Flaggen-Marker
dargestellt: türkische Flaggen für die Verteidiger, britische, französische, australische und
neuseeländische Flaggen für die Angreifer. Jeder Marker trägt eine Zahl für die Truppenstärke,
die im Gefecht heruntergezählt wird. Am Ende steht eine Übersichtskarte aller Schlachten mit den
Flaggen beider Seiten und eine Gefallenen-Bilanz.

1920×1080, 30 fps, 18:00 min, deutscher KI-Sprecher, Orchestermusik und Gefechtsgeräusche.

## Kapitel

| Zeit | Kapitel | Inhalt |
|---|---|---|
| 0:00 | Luftaufnahme & Titel | Anflug auf Çanakkale, Länge (ca. 61 km) und Engstelle (ca. 1,2 km) der Dardanellen |
| 0:50 | 1 · Ein Krieg erfasst die Welt | Bündniskarte 1914 (historische Grenzen), Kriegseintritt des Osmanischen Reichs, Russlands Versorgungsweg, Churchills Plan |
| 2:06 | 2 · Die Festung am Meer | Forts, 10 Minenreihen, Suchscheinwerfer, Angriffe vom 3.11.1914 und 19.2.1915, Minenleger Nusret (26 Minen) |
| 3:42 | 3 · 18. März 1915 | 18 Schlachtschiffe (14 britisch, 4 französisch), Bouvet, Irresistible und Ocean sinken, Seyit Onbaşı, „Çanakkale geçilmez“ |
| 5:26 | 4 · Die Landung | Aufmarsch auf Limnos (ca. 75.000), 5. osmanische Armee (ca. 60.000), Landungen bei Seddülbahir und Arıburnu am 25. April, Mustafa Kemal, Kumkale, Bolayır |
| 8:35 | 5 · Kampf um jeden Meter | Kirte/Krithia I–III, Zığındere, osmanischer Angriff vom 19. Mai, Waffenruhe vom 24. Mai, U-Boot-Krieg |
| 11:07 | 6 · Die Augustoffensive | Kanlısırt/Lone Pine, The Nek, Conkbayırı/Chunuk Bair, Kemals Gegenangriff, Suvla, Anafartalar, Yusufçuk Tepe/Scimitar Hill |
| 14:30 | 7 · Der Rückzug | Bulgariens Kriegseintritt, Schneesturm, Räumung von Arıburnu/Suvla (Dez. 1915) und Seddülbahir (9.1.1916) |
| 15:38 | 8 · Bilanz | Übersichtskarte aller Schlachten mit Flaggen, Gefallene je Nation, Erbe, Atatürk-Gedenkstein, Abspann |

## Aufbau

| Datei | Zweck |
|---|---|
| `narration.py` | Sprechertext (Ortsnamen teils lautschriftlich, damit die KI-Stimme sie richtig spricht) |
| `scenes.py` | Drehbuch als Zeitleiste: Kamerafahrten, Flaggen-Zähler, Pfeile, Schiffe, Einblendungen, alle Zahlen |
| `engine.py` | Render-Engine (Skia): geneigte Kamera über Web-Mercator-Karten, alle Kartenobjekte und Einblendungen |
| `render.py` | Rendert Einzelbilder oder das ganze Video parallel |
| `prep_data.py` | Lädt Satelliten- und Höhendaten und baut die Kartengrundlagen (einmalig) |
| `geo.py` | Geländeabfragen (Land/Wasser, Höhen) zum Platzieren von Objekten |
| `music.py` | Komponiert die Musik (MIDI → FluidSynth) und erzeugt Geräusche, Ducking unter der Sprache |
| `mix_final.py` | Endmischung: Video + Musik + Sprecher → MP4 |
| `voice_durations.json`, `voice_jobs.json` | Längen und Higgsfield-Dateinamen der 32 Sprachaufnahmen |

## Neu rendern

Voraussetzungen: Python 3 mit `skia-python numpy pillow scipy rasterio cairosvg mido`, außerdem
`ffmpeg`, `fluidsynth` und `fluid-soundfont-gm`.

```bash
export CNK_DATA=./data CNK_CACHE=./cache CNK_OUT=./out
python3 prep_data.py                    # Karten bauen (Downloads ca. 1 GB, 5–10 min)
python3 render.py --stills 260,450,990  # Testbilder
python3 render.py --workers 3           # Video ohne Ton (je Prozess ca. 3,6 GB RAM) → out/canakkale_video.mp4
python3 music.py                        # out/music.wav, out/sfx.wav, out/voice_plan.json
# Sprachdateien als voice/00.mp3 … voice/31.mp3 ablegen (Liste in voice_jobs.json), dann:
python3 mix_final.py --video out/canakkale_video.mp4 --bed out/bed.ogg --plan out/voice_plan.json --voice-dir voice --out canakkale-1915.mp4
```

`bed.ogg` ist Musik + Geräusche zusammengemischt:
`ffmpeg -i out/music.wav -i out/sfx.wav -filter_complex amix=inputs=2:normalize=0 -c:a libopus -b:a 256k out/bed.ogg`.
Für `prep_data.py` werden außerdem die Schriften/Flaggen aus `assets/` sowie die GeoJSONs
`world_1914.geojson` (historical-basemaps) und `ne_50m_land.geojson` (Natural Earth) unter `data/geo/` erwartet.

## Zahlen und Quellen

Alle Truppenstärken und Verluste sind gerundet. Die Angaben in der Literatur weichen teils deutlich
voneinander ab, besonders bei den osmanischen Verlusten. Verwendet wurden die gängigen Werte aus:

* Wikipedia (en/de): *Gallipoli campaign*, *Naval operations in the Dardanelles campaign*, *Landing at Anzac Cove*,
  *Landing at Cape Helles*, *First/Second/Third Battle of Krithia*, *Third attack on Anzac Cove*, *Battle of Lone Pine*,
  *Battle of the Nek*, *Battle of Chunuk Bair*, *Landing at Suvla Bay*, *Battle of Scimitar Hill*, *Battle of Kumkale*
* Australian War Memorial / DVA Anzac Portal (Lone Pine 2.277 Verluste, The Nek 372 von 600, 19. Mai, Evakuierung)
* NZHistory (Wellington-Bataillon: von 760 nur rund 70 kampffähig; Gefallene je Land)
* Gallipoli Association, Oxford „Gallipoli chronology“ (Gefallene: Osmanen 56.643 laut Generalstab, Schätzungen bis ca. 87.000;
  Großbritannien 34.072, Indien 1.358, Neufundland 49, Frankreich 9.798, Australien 8.709, Neuseeland 2.721)
* Türkische Quellen zum 18. März (Nusret, 26 Minen in der Bucht von Erenköy; osmanische Verluste wenige Dutzend)

Bewusst mit Vorsicht formuliert: die Geschichte von Seyit Onbaşı („so erzählt die Überlieferung“), Kemals
Befehl vom 25. April und die Taschenuhr (verbreitete Überlieferung) sowie die Atatürk *zugeschriebenen* Worte
auf dem Gedenkstein von Arıburnu (1934). Bei Schlachten, deren Stärke unbekannt ist, zeigt das Video nur die Verluste.

**Hinweis:** Das Satellitenbild ist von 2024. An der Meerenge ist bei weiter Ansicht die moderne
1915-Çanakkale-Brücke als feiner Strich zu sehen.

## Lizenzen und Daten

* Satellitenbilder: enthält modifizierte Copernicus-Sentinel-2-Daten (2024), über AWS Open Data (`sentinel-cogs`)
* Höhendaten: AWS Terrain Tiles (Mapzen; SRTM, GMTED, ETOPO1)
* Grenzen 1914: [historical-basemaps](https://github.com/aourednik/historical-basemaps) (A. Ourednik), Landflächen: Natural Earth
* Flaggen: [flag-icons](https://github.com/lipis/flag-icons) (MIT), Schriften: Cinzel, Barlow (SIL OFL, siehe `assets/`)
* Flagge Österreich-Ungarn 1869 (`assets/flags/ah_1869.svg`, daraus `assets/emblems/ah_flag.png`): OpenFront (CC BY-SA 4.0,
  siehe `assets/flags/LICENSE-OpenFront.txt`)
* Doppeladler Russisches Reich (`assets/emblems/russia_eagle.png`): aus der vom Auftraggeber gelieferten Referenzkarte
  „Europa 1914“ ausgeschnitten und bereinigt
* Sprecher: KI-Stimme „Alistair“ (ElevenLabs v4 über Higgsfield)
* Musik: eigene algorithmische Komposition, gespielt mit dem freien Soundfont FluidR3_GM
