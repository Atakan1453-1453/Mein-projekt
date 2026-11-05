# Amiens 1918 – Der schwarze Tag des deutschen Heeres (Doku, 18 Minuten)

Animierte Karten-Dokumentation auf Deutsch über die Schlacht von Amiens (8.–11. August 1918), im gleichen Stil und
Ablauf wie die Videos zu Gallipoli (`../canakkale`) und Verdun (`../verdun`). Neu: rollende Panzer und Flugzeuge,
Wolken beim Anflug und Nebel am Morgen des 8. August.

* **Panzer:** 1 Modell = 1 Panzer (Mark V, Mark V*, Whippet, Versorgungspanzer, Mark IV, deutscher A7V), in
  Draufsicht perspektivisch auf dem Boden, mit laufenden Ketten, Kettenspuren, Staub, Mündungsfeuer, Ausfällen und
  brennenden Wracks.
* **Flugzeuge:** Staffeln (Sopwith Camel, S.E.5a, SPAD, DH.9, Fokker D.VII, roter Fokker-Dreidecker) mit Schatten am
  Boden, Kurvenflug im Luftkampf, Leuchtspur, Absturz mit Rauchfahne, Bombenabwürfe, Fallschirm-Munitionsabwurf (Le Hamel).
* **Wolken:** drei Schichten in verschiedenen Höhen. Beim Herabzoomen wachsen sie, ziehen zur Seite oder fliegen durch die
  Kamera; in den Nahszenen liegt die Kamera unter den Wolken.
* **Flaggen:** auf den Übersichtskarten Länder mit ihren Flaggen (Kaiserreich, Österreich-Ungarn, Osmanisches Reich,
  Bulgarien, Frankreich, Großbritannien, Italien, Russland); in den Kampfszenen nur leichte Rot/Blau-Färbung.
  Kanada mit der Red Ensign von 1918.
* **Musik:** neu komponiert (e-Moll, eigenes Leitmotiv E–H–A–G–E–Dis–E), Marsch, Fanfare, Pizzicato, Flöte im
  Dreivierteltakt für die Luftkämpfe, Hymne in G-Dur am Ende; Geräusche inkl. Panzer- und Flugzeugmotoren.

1920×1080, 30 fps, 18:01 min, deutscher KI-Sprecher („Alistair“). Abspann: Produzent Atakan Zengin · Kanal WarAZ.

## Aufbau

| Datei | Zweck |
|---|---|
| `narration.py` | Sprechertext (32 Abschnitte) |
| `vgeo.py` | Orte, Frontverläufe bei Amiens (März–August 1918), Westfront 1918 zu acht Zeitpunkten, Routen |
| `scenes.py` | Drehbuch als Zeitleiste (zwei Durchläufe für Vorgriffe auf spätere Abschnitte) |
| `armor.py` | Panzer, Flugzeuge, Fallschirme, Wolken, Nebel, Nacht, Westfront-Morphing |
| `engine.py`, `render.py`, `render_chunks.py` | Render-Engine (aus `../verdun`) |
| `prep_data.py` | Satellit (Sentinel-2, 12.8.2025), Höhendaten, Trichtertextur; Übersichtskarten aus dem Verdun-Cache |
| `music.py`, `mix_final.py` | Musik (MIDI → FluidSynth) und Geräusche, Endmischung mit Sprecher |

## Zahlen und Quellen (gerundet, die Literatur weicht ab)

* Unternehmen Michael ab 21.3.1918: über 6.000 Geschütze, Vorstoß bis ca. 60 km; Verluste bis Anfang April ca. 240.000
  (deutsch) und ca. 250.000 (britisch und französisch)
* 21.4.1918 Richthofen bei Vaux-sur-Somme abgeschossen; 24.4.1918 erstes Panzergefecht bei Villers-Bretonneux
  (3 Mark IV gegen 3 A7V, Lt. Frank Mitchell, A7V „Nixe“); Nacht zum 25.4. australischer Gegenangriff
* 4.7.1918 Le Hamel (Monash, ca. 60 Mark V, Fallschirm-Munitionsabwurf, erste US-Einheiten, „93 Minuten“)
* 8.8.1918: über 2.000 Geschütze, ca. 342 Mark V/V*, 72 Whippets, 120 Versorgungspanzer; ca. 800 britische und
  1.100 französische Flugzeuge gegen ca. 365 deutsche; Kanadier ca. 13 km, Australier ca. 11 km
* Deutsche Verluste am 8.8.: ca. 27.000, darunter mehr als 12.000 Gefangene, ca. 400 Geschütze
* RAF am 8.8.: fast 100 Maschinen abgeschossen oder schwer beschädigt (Angriffe auf die Somme-Brücken)
* Gesamtverluste 8.–11.8.: Alliierte ca. 46.000 (je etwa zur Hälfte britisch/Dominions und französisch), Deutsche ca. 75.000
  inkl. fast 30.000 Gefangene
* 29.9.1918 Durchbruch durch die Siegfriedstellung am St-Quentin-Kanal; 11.11.1918 Waffenstillstand von Compiègne
* Gedenkfeier in der Kathedrale von Amiens am 8.8.2018 (u. a. Joachim Gauck)

Verwendet u. a.: Australian War Memorial, The Tank Museum, Canadian Encyclopedia, Vimy Foundation, Western Front
Association, Britannica, Wikipedia-Artikel zu den Schlachten. Das Kaiser-Zitat ist nur überliefert.
Frontverläufe vereinfacht.

## Lizenzen und Daten

* Satellitenbilder: enthält modifizierte Copernicus-Sentinel-2-Daten (2025), über AWS Open Data (`sentinel-cogs`)
* Übersichtskarten: © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by
  ESA WorldCover consortium (CC BY 4.0)
* Höhendaten: AWS Terrain Tiles (Mapzen); Grenzen 1914: historical-basemaps (A. Ourednik); Landflächen: Natural Earth
* Flaggen: flag-icons (MIT), eigene Red Ensign Kanadas; Österreich-Ungarn: OpenFront (CC BY-SA 4.0); Schriften: Cinzel, Barlow (SIL OFL)
* Sprecher: KI-Stimme „Alistair“ (ElevenLabs v4 über Higgsfield); Musik: eigene Komposition (FluidR3_GM)
