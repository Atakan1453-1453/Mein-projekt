# Verdun 1916 – Die Hölle an der Maas (Doku, 18 Minuten)

Animierte Karten-Dokumentation auf Deutsch über die Schlacht um Verdun (21. Februar – 18. Dezember 1916),
im gleichen Stil und Ablauf wie das Çanakkale-Video in `../canakkale`. Das Video beginnt mit einer Luftaufnahme
über Verdun und fliegt zu jedem Ereignis. Truppen erscheinen als Flaggen-Marker mit Zahlen (Deutsches Kaiserreich
Schwarz-Weiß-Rot, Frankreich Trikolore) und als Figuren (1 Figur = 1 Soldat: deutsch rot, französisch blau), die im
Gefecht fallen. Der Frontverlauf wird über das ganze Jahr animiert. Hinter der Linie liegt auf jeder Seite hauchdünn die
Flagge des Landes (deutsch gehaltenes Gebiet Schwarz-Weiß-Rot, französisches Trikolore), in der Übersichtskarte kräftig.
Alle Verbände bleiben an der Front stehen und rücken mit ihr mit; Gefallene verblassen nach einigen Sekunden.
Wo die Granaten einschlagen, brennen die Wälder. Die Wälder verwandeln sich nach und nach in eine Trichterwüste.
Die Kamera zoomt nahtlos von der Nahansicht bis zur Europakarte (Satellit → ESA WorldCover in Naturfarben).

1920×1080, 30 fps, 18:00 min, deutscher KI-Sprecher („Alistair“), eigene Orchestermusik und Gefechtsgeräusche.
Abspann: Produzent Atakan Zengin · Kanal WarAZ.

## Kapitel

| Zeit | Kapitel | Inhalt |
|---|---|---|
| 0:00 | Luftaufnahme & Titel | Anflug über die Maas auf Verdun, Fort Douaumont, Trichterlandschaft |
| 0:52 | 1 · Ein Krieg erfasst die Welt | Bündniskarte 1914 mit Flaggen, Vormarsch durch Belgien, Marne, Westfront, Falkenhayns Plan |
| 2:30 | 2 · Die Festung Verdun | Ring der Forts, Abzug der Geschütze 1915, Frontbogen, Bahnlinien, Unternehmen Gericht |
| 4:16 | 3 · 21. Februar 1916 | Trommelfeuer, Bois des Caures (Driant), Vormarsch, Fall von Fort Douaumont |
| 6:29 | 4 · Der heilige Weg | Pétain, Voie Sacrée (Lastwagen-Konvoi), Noria |
| 8:07 | 5 · Die Hölle von Verdun | Toter Mann und Höhe 304, Trichterwüste, Mangins Angriff auf Douaumont |
| 9:48 | 6 · Kampf um die Forts | Fort Vaux und Raynals Brieftaube, Grünkreuz, Thiaumont und Fleury, Somme/Brussilow, Fort Souville |
| 12:58 | 7 · Die Gegenoffensive | Falkenhayn abgelöst, Eisenbahngeschütze, Feuerwalze, Douaumont und Vaux zurück, Dezemberoffensive |
| 15:22 | 8 · Bilanz | Übersichtskarte aller Schlachten, Verluste, zerstörte Dörfer, Beinhaus, Kohl und Mitterrand 1984, Abspann |


## Aufbau

| Datei | Zweck |
|---|---|
| `narration.py` | Sprechertext (32 Abschnitte) |
| `vgeo.py` | Orte, Forts, Maas, Frontverläufe 1916, Trichterzonen, Voie Sacrée, Westfront |
| `scenes.py` | Drehbuch als Zeitleiste: Kamerafahrten, Frontanimation, Flaggen-Zähler, Figuren, Einblendungen |
| `engine.py` | Render-Engine (aus `../canakkale`), erweitert um FrontMap, CraterField, Barrage/Feuerwalze, GasCloud, Convoy, Bird, VFort, Guns, ShellArcs, TerritoryFlags, Burning, Rain, BigWord, FrontPulse |
| `prep_data.py` | Satellit (Sentinel-2, 11.8.2025), Höhendaten, Trichtertextur, Europa/Übergangskarte aus ESA WorldCover |
| `render.py`, `render_chunks.py` | Einzelbilder / Video in Stücken rendern |
| `music.py`, `mix_final.py` | Musik (MIDI → FluidSynth) und Geräusche, Endmischung mit Sprecher |
| `voice_durations.json`, `voice_jobs.json` | Längen und Higgsfield-Dateinamen der Sprachaufnahmen |

Neu rendern wie in `../canakkale/README.md` beschrieben (`prep_data.py L2 L3 craters worldcover`, dann `render_chunks.py`,
`music.py`, `mix_final.py`).

## Zahlen und Quellen

Alle Zahlen sind gerundet; die Literatur weicht teils deutlich ab. Wo Stärken nur geschätzt werden können,
steht im Bild „ca.“. Verwendet wurden die gängigen Werte, u. a. aus Britannica, Mémorial de Verdun, Chemins de
mémoire (französisches Verteidigungsministerium), Musée de l'Armée, Bundesregierung (Archiv 1984) und Wikipedia-Artikeln
zur Schlacht, zu Fort Douaumont, Fort Vaux, Fort Souville, dem Bois des Caures und der Voie Sacrée.

* Angriff 21.2.1916: mehr als 1.200 deutsche Geschütze, 9 Divisionen, Front ca. 40 km (Bois d'Avocourt – Étain);
  Stärke der Angreifer (ca. 140.000) und Verteidiger (ca. 34.000, „34 Bataillone“) sind Schätzungen
* Bois des Caures: ca. 1.200 Jäger unter Driant, nur gut 100 kehrten zurück
* Fort Douaumont am 25.2. von Männern des Brandenburgischen IR 24 ohne Kampf genommen (Besatzung ca. 57)
* Voie Sacrée: Spitze ein Fahrzeug alle 14 Sekunden; im Schnitt täglich ca. 13.000 Soldaten, 6.400 t Material
  und 1.500 t Munition (Chemins de mémoire)
* Höhe 304 fiel Anfang Mai, Toter Mann Ende Mai (Daten je nach Quelle 24.–29. Mai)
* Fort Vaux 1.–7. Juni, ca. 600 Mann im Fort, letzte Taube „Le Vaillant“ am 4. Juni
* Grünkreuz (Diphosgen) 22./23. Juni, über 100.000 Granaten; Fleury wechselte 16-mal den Besitzer
* 11./12. Juli: letzter Angriff auf Fort Souville
* 24. Oktober: Douaumont zurückerobert, ca. 6.000 Gefangene; 2. November: Vaux; 15.–18. Dezember: ca. 11.000
  Gefangene, 115 Geschütze
* Verluste: Frankreich ca. 377.000, Deutschland ca. 337.000 (Heer/Naumann 2000), zusammen ca. 714.000;
  rund 300.000 Tote (ca. 163.000 französische, 143.000 deutsche)
* Beinhaus von Douaumont: Gebeine von rund 130.000 Unbekannten; Kohl und Mitterrand am 22.9.1984

Vorsichtig formuliert: Falkenhayns „Weihnachtsdenkschrift“ ist nur aus seinen Erinnerungen bekannt; die Truppenstärken
in einzelnen Gefechten (Figuren) sind Größenordnungen, keine exakten Zahlen. Die Frontverläufe sind vereinfacht.

## Lizenzen und Daten

* Satellitenbilder: enthält modifizierte Copernicus-Sentinel-2-Daten (2025), über AWS Open Data (`sentinel-cogs`)
* Übersichtskarten: © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by
  ESA WorldCover consortium (CC BY 4.0), eingefärbt passend zum Satellitenbild (`prep_data.py worldcover`)
* Höhendaten: AWS Terrain Tiles (Mapzen; SRTM, GMTED, ETOPO1)
* Grenzen 1914: [historical-basemaps](https://github.com/aourednik/historical-basemaps) (A. Ourednik), Landflächen: Natural Earth
* Flaggen: [flag-icons](https://github.com/lipis/flag-icons) (MIT); Österreich-Ungarn 1869: OpenFront (CC BY-SA 4.0);
  Zarenadler aus der Referenzkarte des Auftraggebers; Schriften: Cinzel, Barlow (SIL OFL)
* Sprecher: KI-Stimme „Alistair“ (ElevenLabs v4 über Higgsfield); Musik: eigene Komposition (FluidR3_GM)
