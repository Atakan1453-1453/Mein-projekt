"""Alle Texte und Fakten des Videos an einer Stelle – hier anpassen und neu rendern.

Quellen (Recherche Oktober 2026, siehe README.md):
- galeriekoenigshof.de (Center-Website: Shops, „über 20 Shops … über 400 Parkplätze“,
  Kernöffnungszeiten Mo–Sa 10–19 Uhr, Parkhaus 24 h geöffnet)
- Stadt Mettmann / ILG Gruppe / Radio Neandertal / Schaufenster Mettmann
  (Wiedereröffnung 7. November 2019, 14 Monate Umbau, über 10 Mio. € Investition,
  schrankenloses Parkhaus, Bezahlung am Automaten oder per App)
- Gleeds-Projektseite (rund 15.000 m² Mietfläche)
- Phoenix Development (Gebäude von 1972, Hertie bis 2009)
"""

NAME = "Galerie Königshof"
CITY = "Mettmann"
TAGLINE = "Shopping im Herzen der Stadt"

ADDRESS_STREET = "Talstraße 10"
ADDRESS_CITY = "40822 Mettmann"
WEBSITE = "galeriekoenigshof.de"

# (Zahl, Präfix, Suffix, Beschriftung, Unterzeile)
STATS = [
    (20, "", "+", "Shops", "plus Gastronomie & Services"),
    (400, "", "+", "Parkplätze", "im eigenen Parkhaus"),
    (15000, "", "", "m² Mietfläche", "circa"),
]
STATS_NOTE = "Angaben laut Center-Website bzw. Projektangaben"

# (Jahr, Titel, Unterzeile)
TIMELINE = [
    ("1972", "Kaufhaus an der Talstraße", "später Hertie – bis 2009"),
    ("nach 2009", "Umbau zur Königshof-Galerie", "auf dem früheren Hertie-Areal"),
    ("2019", "Neustart als Galerie Königshof", "Wiedereröffnung am 7. November"),
]
RELAUNCH_FACTS = [
    "14 Monate Umbau im laufenden Betrieb",
    "über 10 Mio. € Investition",
]

# (Kategorie, Name) – Auswahl laut Shop-Verzeichnis der Center-Website
SHOPS = [
    ("Mode", "H&M"),
    ("Schuhe", "Deichmann"),
    ("Mode", "Takko Fashion"),
    ("Familie", "Ernsting's family"),
    ("Drogerie", "dm"),
    ("Apotheke", "easyApotheke"),
    ("Bücher", "Thalia"),
    ("Blumen", "Ambiente\nBlumen & mehr"),
    ("Presse & Tabak", "kkiosk"),
    ("Gastronomie", "Asia Friends"),
]
SHOPS_NOTE = "Auswahl · Mieterangebot kann sich ändern"

PARKING = [
    "Über 400 Parkplätze im Parkhaus",
    "Schrankenlose Ein- und Ausfahrt",
    "Bezahlen am Automaten oder per App",
    "Parkhaus 24 Stunden geöffnet",
]

HOURS_DAYS = "Montag – Samstag"
HOURS_TIME = "10:00 – 19:00 Uhr"
HOURS_NOTE = "Kernöffnungszeiten · einzelne Shops mit abweichenden Zeiten"

CLOSING = "Wir freuen uns auf Ihren Besuch!"
