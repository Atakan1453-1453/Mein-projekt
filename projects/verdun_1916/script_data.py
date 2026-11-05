"""Skript + Szenenliste „Verdun 1916“ (WarAZ).

Ein Eintrag = ein Sprecher-Absatz = eine Stimm-Generierung.
  id     – Absatz-ID (Dateiname der Stimmspur: voice/P01.wav …)
  ch     – Kapitel-Nummer (siehe CHAPTERS)
  tts    – Sprechertext, so geschrieben, wie er gesprochen wird
           (französische Namen in Lautschrift, Zahlen ausgeschrieben)
  map    – Kartenaktion / Bild
  ins    – Einblendung
  snd    – Musik / Geräusche
  date   – Datum für den Zähler (TT.MM.) – leer = unverändert

Kennzeichnung KI-Clips: [KI-1] … [KI-4]. Alles andere ist Code-Animation.
"""

CHAPTERS = {
    1: "Hook",
    2: "Warum Verdun?",
    3: "Der Angriff",
    4: "Die Heilige Straße",
    5: "Die Hölle",
    6: "Die Wende",
    7: "Finale",
    8: "Outro",
}

# Lautschrift für den Sprechertext (Anzeige-Schreibweise -> gesprochen)
PRONUNCIATION = {
    "Verdun": "Wer-döng",
    "Douaumont": "Du-o-mong",
    "Vaux": "Woh",
    "Souville": "Su-wil",
    "Fleury": "Flö-ri",
    "Pétain": "Pe-täng",
    "Nivelle": "Ni-well",
    "Mangin": "Mang-schäng",
    "Driant": "Dri-ang",
    "Émile": "E-mil",
    "Raynal": "Rä-nal",
    "Bois des Caures": "Boa de Kohr",
    "Voie Sacrée": "Woa Sa-kreh",
    "Bar-le-Duc": "Bar-lö-Dük",
    "Louvemont": "Luv-mong",
    "Bezonvaux": "Be-song-woh",
    "Pour le Mérite": "Pur lö Me-riht",
    "Courage ! On les aura !": "Ku-rahsch! Ong lehs o-rah!",
    "Ils ne passeront pas !": "Il nö pass-rong pa!",
    "Noria": "No-ria",
}

P = []


def add(id, ch, tts, map, ins="", snd="", date=""):
    P.append(dict(id=id, ch=ch, tts=tts, map=map, ins=ins, snd=snd, date=date))


# ---------------------------------------------------------------- 1 HOOK
add("P01", 1,
    "Einundzwanzigster Februar neunzehnhundertsechzehn. Kurz nach sieben Uhr morgens. "
    "Nördlich von Wer-döng liegt Schnee auf den Wäldern. Es ist still.",
    "Schwarz → Karte blendet auf, tief geneigt, Morgendämmerung, Schneedecke, leichter Nebel. "
    "Langsamer Flug über verschneite Wälder nördlich der Stadt. Französische Figuren (horizontblau) in Stellung, "
    "Rauchfahne aus einem Unterstand.",
    "Datum zentral: „21. FEBRUAR 1916 · 07:15“; Zähler unten links erscheint: TAG 1",
    "Wind, ferne Krähe, Stille. Musik: tiefer Ton schwillt an (M1 „Morgengrauen“)",
    "21.02.")
add("P02", 1,
    "Dann reißt der Himmel auf. Mehr als zwölfhundert deutsche Geschütze feuern auf die französischen Stellungen "
    "nördlich der Stadt. Stundenlang. Ohne Pause.",
    "Mündungsblitze am oberen Kartenrand: Reihe deutscher Geschütze (feldgrau). Einschläge wandern über die "
    "Wälder, Schnee wird braun. [KI-1] „Trommelfeuer im Morgengrauen“ (4–5 s): Kamera taucht in die Karte ein, "
    "Geschützreihe feuert im Dämmerlicht, dann zurück auf die Karte.",
    "Zahl-Karte: „1.200+ GESCHÜTZE“",
    "Erster Donnerschlag nach 0,5 s Stille, dann Trommelfeuer-Teppich, tiefer Bass-Puls",
    "")
add("P03", 1,
    "Es ist der Beginn der längsten Schlacht des Ersten Weltkriegs. Dreihundertzwei Tage später steht die Front "
    "fast wieder dort, wo sie an diesem Morgen stand. Und rund dreihunderttausend Menschen sind tot.",
    "Kamera reißt nach oben in den Überblick. Zeitraffer-Vorschau: Frontlinie zuckt vor und zurück, "
    "Trichterfeld breitet sich aus, Wälder verschwinden; Zähler rast von TAG 1 bis TAG 302 und springt zurück.",
    "„302 TAGE“ → „≈ 300.000 TOTE“ (Zahl-Karte, rot unterstrichen)",
    "Trommelfeuer gedämpft wie unter Wasser, Musik: Streicherfläche",
    "")
add("P04", 1,
    "Warum? Warum sterben hier so viele Menschen für ein paar Kilometer Land? Genau das klären wir heute. "
    "Auf dieser Karte.",
    "Zurück zum 21. Februar, Karte wieder unversehrt. Kamera schwebt zurück auf Verdun.",
    "Frage-Karte: „WARUM STARBEN HIER ~300.000 MENSCHEN FÜR EIN PAAR KILOMETER?“ → Titel „VERDUN 1916“ "
    "(Intro-Vorlage, 3 s)",
    "Musik bricht ab auf „Warum?“, Titel-Schlag (Pauke), dann ruhiger Puls",
    "")

# ---------------------------------------------------------------- 2 WARUM VERDUN?
add("P05", 2,
    "Schauen wir uns zuerst an, wo wir sind. Das ist Wer-döng. Eine kleine Stadt an der Maas, "
    "im Nordosten Frankreichs.",
    "Zoom-out bis Frankreich-Umriss (Inset oben rechts), Pin auf Verdun, dann Zoom hinein: Maas schlängelt sich "
    "von Süd nach Nord, Stadt mit Zitadelle.",
    "Kapitelkarte „1 · WARUM VERDUN?“; Orts-Label „VERDUN“, „MAAS“",
    "Musik M2 „Lage“ (ruhig, tickend), Wasserrauschen leise beim Fluss",
    "")
add("P06", 2,
    "Seit Herbst neunzehnhundertvierzehn ragt die Front hier wie ein Bogen in die deutschen Linien hinein. "
    "Im Norden, im Osten und im Südosten stehen Deutsche. Offen ist nur der Weg nach Südwesten.",
    "Frontlinie zeichnet sich als Bogen um Verdun (Linie wächst animiert). Fläche dahinter feldgrau getönt. "
    "Deutsche Figuren erscheinen im Norden, Osten, Südosten; Pfeil nach Südwesten leuchtet blau.",
    "Label „FRONTBOGEN VON VERDUN“, Pfeil-Label „EINZIGER OFFENER WEG“",
    "Zeichen-Sound beim Linienziehen",
    "")
add("P07", 2,
    "Um die Stadt liegt ein Ring aus Festungen. Fast vierzig Forts und Werke, verteilt auf Hügeln und "
    "Waldrücken. Das größte von ihnen heißt Fort Du-o-mong. Merk dir diesen Namen.",
    "Kreisfahrt um Verdun: Fort-Symbole ploppen nacheinander auf den Höhen auf (Ring). Schwenk und Zoom auf "
    "Douaumont, Fort-Symbol größer, leichter Glanz.",
    "Label „FESTUNGSRING · ~40 FORTS & WERKE“; großes Orts-Label „FORT DOUAUMONT“",
    "„Plopp“-Akzente pro Fort, tiefer Ton bei Douaumont",
    "")
add("P08", 2,
    "Für Frankreich ist Wer-döng mehr als eine Festung. Es ist ein Symbol. Siebzehnhundertzweiundneunzig fiel "
    "die Stadt an die Preußen. Achtzehnhundertsiebzig an die Deutschen. Ein drittes Mal darf das nicht passieren.",
    "Kamera zurück auf die Stadt. Zwei „Geister-Fahnen“ (preußisch/deutsch) wehen kurz über der Zitadelle, "
    "dann französische Trikolore.",
    "Jahreszahlen-Stempel „1792“ und „1870“, durchgestrichen-Stil; dann „1916?“",
    "Zwei Stempel-Schläge, dann Trommelwirbel leise",
    "")
add("P09", 2,
    "Das Problem: Die Festung ist fast leer. Neunzehnhundertvierzehn haben deutsche Riesengeschütze die belgischen Forts in wenigen Tagen zerschlagen. Die französische Führung folgert daraus: Forts sind veraltet.",
    "Inset-Karte oben links: Belgien mit Lüttich/Namur, zwei Fort-Symbole zerbrechen. Zurück nach Verdun.",
    "Labels „LÜTTICH · NAMUR · AUG. 1914“",
    "Zwei schwere Einschläge (gedämpft, fern)",
    "")
add("P10", 2,
    "Also werden die Forts von Wer-döng neunzehnhundertfünfzehn ausgeräumt. Vierundfünfzig Batterien werden abgezogen. Der Kommandant vor Ort protestiert. Ohne Erfolg.",
    "Geschütz-Figuren verlassen die Forts und rollen in einer Kolonne vom Kartenrand weg. Forts werden grau / "
    "„hohl“ (Symbol nur noch als Umriss).",
    "Zahl-Karte „− 54 BATTERIEN“, Datum-Stempel „AUGUST 1915“",
    "Rollgeräusche, Pferdehufe; dry: kurzer Plopp beim „Ohne Erfolg“",
    "")
add("P11", 2,
    "Auf der anderen Seite der Karte sitzt Erich von Falkenhayn, Chef der Obersten Heeresleitung. Im Westen bewegt sich seit über einem Jahr fast nichts. Sein Plan: ein Angriff auf Wer-döng. Deckname: Unternehmen Gericht.",
    "Schwenk nach Nordosten auf die deutsche Seite. Kartentisch-Look: Kommandozelt-Symbol, Porträt-Medaillon "
    "Falkenhayn (gezeichnete Silhouette, kein Foto). Rote Planungspfeile zeichnen sich auf Verdun.",
    "Namens-Einblender „ERICH VON FALKENHAYN · CHEF DER OHL“; Stempel „UNTERNEHMEN GERICHT“",
    "Musik M3 „Planung“ (dunkler, Uhr-Ticken), Feder-Kratzen",
    "")
add("P12", 2,
    "Ausführen soll ihn die fünfte Armee. Ihr Oberbefehlshaber ist der Sohn des Kaisers: Kronprinz Wilhelm.",
    "Deutsche Infanterie-, Artillerie- und Fesselballon-Figuren sammeln sich in den Wäldern nördlich und "
    "nordöstlich (Truppen marschieren ein, Ballons steigen).",
    "Einblender „5. ARMEE · KRONPRINZ WILHELM“",
    "Marschtritt leise, Ballonwinde",
    "")
add("P13", 2,
    "Und jetzt wird es interessant. Nach dem Krieg schreibt Falkenhayn, es sei ihm gar nicht in erster Linie um die Stadt gegangen. Frankreich sollte hier ausbluten. Bis seine Armee zusammenbricht.",
    "Kamera kippt flacher. Blaue Figuren strömen in Richtung Verdun und „verblassen“ (Symbolik), Fläche "
    "rötet sich leicht.",
    "Zitat-Karte (Lesetext, nicht gesprochen): „… so werden sich Frankreichs Kräfte verbluten …“ "
    "– Falkenhayn, Memoiren 1920",
    "Musik fällt auf einen einzigen tiefen Ton",
    "")
add("P14", 2,
    "Als Beweis nennt er eine geheime Denkschrift an den Kaiser, Weihnachten neunzehnhundertfünfzehn. Das Problem: Dieses Dokument hat nie jemand gefunden.",
    "Ein Dokument-Symbol erscheint über dem deutschen Hauptquartier und löst sich in Rauch auf.",
    "Stempel „WEIHNACHTSDENKSCHRIFT 1915“ → „ORIGINAL NIE GEFUNDEN“",
    "Papierrascheln, dann Stille",
    "")
add("P15", 2,
    "Ob der Plan damals wirklich so lautete, ist unter Historikern umstritten. Merk dir das. Denn genau hier steckt ein Teil der Antwort.",
    "Fragezeichen-Marker bleibt über dem Hauptquartier stehen (kehrt im Finale wieder). Langsame Fahrt zurück "
    "zur Front im Schnee.",
    "Label „UMSTRITTEN“ (gelbes Warn-Badge, Stil für alle umstrittenen Punkte)",
    "Uhr-Ticken wird lauter → harter Schnitt",
    "")

# ---------------------------------------------------------------- 3 DER ANGRIFF
add("P16", 3,
    "Zurück zum einundzwanzigsten Februar. Die Granaten fallen so dicht, dass sich die Landschaft verändert. "
    "Wälder werden zu Stümpfen. Gräben verschwinden einfach.",
    "Nahflug über den Bois des Caures: Dauerfeuer, Explosionen, Rauch. Wald-Textur wird live zu Stümpfen, "
    "erste Trichter. Zerstörung Stufe 1.",
    "Kapitelkarte „2 · DER ANGRIFF“; Zähler: 21.02.1916 · TAG 1",
    "Trommelfeuer (nah), Splitterregen, Musik M4 „Angriff“ (treibende Pauken)",
    "21.02.")
add("P17", 3,
    "Am Nachmittag gehen die ersten deutschen Stoßtrupps vor. Sie erwarten, dass dort vorne niemand mehr lebt. "
    "Sie irren sich.",
    "Feldgraue Infanterie-Figuren lösen sich aus dem Wald, bewegen sich in kleinen Gruppen nach Süden. "
    "Bei „Sie irren sich“: Mündungsfeuer aus dem Wald, blaue Figuren tauchen aus den Trichtern auf.",
    "",
    "Pfiff, MG-Feuer setzt ein",
    "")
add("P18", 3,
    "Im Boa de Kohr, einem Waldstück an der Spitze der Front, liegen rund zwölfhundert französische Jäger. "
    "Ihr Kommandeur: Oberstleutnant E-mil Dri-ang. Sie halten bis zum nächsten Tag.",
    "Zoom auf das Waldstück. Blaue Figuren in Kreis-Formation. Deutsche Pfeile prallen zweimal ab.",
    "Orts-Label „BOIS DES CAURES“; Einblender „OBERSTLEUTNANT ÉMILE DRIANT · ~1.200 JÄGER“",
    "MG, Gewehrfeuer, Granaten nah",
    "")
add("P19", 3,
    "Am zweiten Tag fällt Dri-ang. Sein Widerstand bringt den deutschen Zeitplan durcheinander. Aufhalten kann er "
    "den Angriff nicht. Dorf um Dorf fällt. Die Front biegt sich nach Süden.",
    "Blaue Figuren weichen zurück. Frontlinie wird nach Süden gedrückt; Dörfer (Haumont, Beaumont, Samogneux) "
    "wechseln nacheinander die Farbe, Häuser-Sprites → Ruinen.",
    "Zähler 22.02. TAG 2 → 24.02. TAG 4; Dorf-Labels poppen beim Fallen auf",
    "Musik treibt, Einschläge im Takt",
    "22.02.")
add("P20", 3,
    "Dann kommt der fünfundzwanzigste Februar. Tag fünf. Erinnerst du dich? Fort Du-o-mong. "
    "Das größte Fort im ganzen Ring.",
    "Kamera fliegt im Schneetreiben auf Fort Douaumont zu, Fort füllt das Bild (2.5D, Schatten).",
    "Zähler 25.02.1916 · TAG 5; Orts-Label „FORT DOUAUMONT“ (wiederkehrendes Design aus Kap. 1)",
    "Musik bricht ab. Wind, Schnee, fernes Feuer",
    "25.02.")
add("P21", 3,
    "Ein kleiner deutscher Trupp, etwa zehn Pioniere unter Feldwebel Kunze, arbeitet sich bei Schneetreiben an "
    "den Graben heran. Niemand schießt auf sie.",
    "Ca. 10 winzige feldgraue Figuren schleichen auf das Fort zu. "
    "[KI-2] „Fort Douaumont im Schneetreiben“ (4–5 s): Silhouetten an der Betonmauer, Schnee, Stille.",
    "Einblender „FELDWEBEL KUNZE · ~10 PIONIERE“",
    "Schritte im Schnee, Herzschlag-Puls",
    "")
add("P22", 3,
    "Kunze klettert hinein. Die Gänge sind leer. Die kleine Restbesatzung hat sich vor dem Beschuss in die Tiefe zurückgezogen. Ranghöchster Franzose im Fort: ein Unteroffizier.",
    "Schnittbild-Overlay: Fort als Querschnitt (Code-Grafik), Figur bewegt sich durch Gänge; unten wenige blaue "
    "Figuren in der Tiefe.",
    "",
    "Hall, Tropfen, Echo-Schritte",
    "")
add("P23", 3,
    "Kurz darauf folgt Leutnant Radtke mit rund zwanzig Mann. Dann weitere Offiziere. Das stärkste Fort von "
    "Wer-döng wechselt den Besitzer. Ohne dass ein Schuss fällt.",
    "Weitere feldgraue Gruppen strömen hinein. Fort-Symbol färbt sich von Blau zu Feldgrau, Fahne wechselt.",
    "Groß: „FORT DOUAUMONT FÄLLT · OHNE EINEN SCHUSS“",
    "Ein einzelner Glockenschlag, Musik-Stich",
    "")
add("P24", 3,
    "Den höchsten Orden bekommen übrigens nicht die Männer, die zuerst drin waren. Den Pur lö Me-riht erhält Oberleutnant von Brandis, der erst später kam.",
    "Drei Namens-Kärtchen über dem Fort: Orden-Symbol wandert zu „von Brandis“, die zwei anderen grauen aus.",
    "Einblender „POUR LE MÉRITE → OBLT. VON BRANDIS“",
    "Trockener Akzent (Pizzicato)",
    "")
add("P25", 3,
    "In Wer-döng plant der Befehlshaber bereits, das ganze rechte Maasufer aufzugeben. Frankreich wankt. "
    "Und jetzt braucht es jemanden, der nicht wankt.",
    "Zoom-out: Deutscher Keil steht vor Verdun. Blaue Rückzugspfeile über die Maas zeichnen sich gestrichelt. "
    "Bild friert leicht ein (Mini-Cliffhanger).",
    "„FRANKREICH WANKT“ (Schlagzeile, rot), Zähler TAG 5",
    "Musik steigt an, Abbruch auf Schlag",
    "")

# ---------------------------------------------------------------- 4 HEILIGE STRASSE
add("P26", 4,
    "Noch am selben Tag wird ein General nach Wer-döng geschickt: Philippe Pe-täng, neunundfünfzig Jahre alt. "
    "Er gilt als vorsichtig. Er glaubt an Artillerie, nicht an Heldenmut.",
    "Ein einzelnes Auto-Symbol fährt nachts durch Schneesturm nach Souilly (Hauptquartier-Marker).",
    "Kapitelkarte „3 · DIE HEILIGE STRASSE“; Einblender „GENERAL PHILIPPE PÉTAIN · 2. ARMEE“",
    "Motor, Wind, Musik M5 „Lebensader“ (pulsierend, hoffnungsvoll-dunkel)",
    "25.02.")
add("P27", 4,
    "Sein größtes Problem ist nicht der Feind. Es ist der Nachschub. Die Bahnlinien nach Wer-döng sind abgeschnitten "
    "oder liegen unter Feuer. Übrig bleibt eine Landstraße. Von Bar-lö-Dük nach Wer-döng. Gut siebzig Kilometer.",
    "Großer Zoom-out nach Süden bis Bar-le-Duc. Bahnlinien rot durchgekreuzt. Eine Straße zeichnet sich von "
    "Bar-le-Duc nach Norden.",
    "Labels „BAR-LE-DUC“, „SOUILLY“, „~72 KM“",
    "Zeichen-Sound, Bahn-Signalton (abgeschnitten)",
    "")
add("P28", 4,
    "Pe-täng macht daraus eine Lebensader. Tausende Lastwagen fahren Tag und Nacht, in beide Richtungen. "
    "Zur Spitzenzeit rollt alle vierzehn Sekunden ein Fahrzeug vorbei. Das sind rund sechstausend am Tag.",
    "Lastwagen-Figuren rollen in zwei Kolonnen; Tag-Nacht-Wechsel über der Karte. "
    "[KI-3] „Lastwagenkolonne nachts auf der Heiligen Straße“ (4–5 s): Scheinwerfer, Schlamm, Soldaten auf Ladeflächen.",
    "Zähler-Gimmick: Mini-Uhr „14 s“ tickt, bei jedem Ticken ein Lastwagen; „≈ 6.000 / TAG“",
    "Motorenbrummen in Wellen",
    "")
add("P29", 4,
    "Die Straße hält das kaum aus. Tausende Männer schaufeln ohne Pause Schotter unter die Räder. Wer liegen bleibt, wird zur Seite geschoben. Die Kolonne darf nie stehen.",
    "Nahansicht: Arbeiter-Figuren am Straßenrand; ein Lastwagen kippt zur Seite, Kolonne fließt weiter.",
    "„~8.000 MANN STRASSENBAU“",
    "Schaufeln, Steine, Motoren",
    "")
add("P30", 4,
    "Im April gibt ein Schriftsteller der Straße ihren Namen: Woa Sa-kreh. Die Heilige Straße.",
    "Straße beginnt zu glühen (goldene Linie), Kamera fährt an ihr entlang nach Norden.",
    "Großer Titel „VOIE SACRÉE · DIE HEILIGE STRASSE“",
    "Musik öffnet sich (Akkordwechsel)",
    "")
add("P31", 4,
    "Und Pe-täng hat noch eine Idee. Keine Division soll zu lange in dieser Hölle bleiben. Die Truppen werden ständig ausgetauscht. Die Franzosen nennen das No-ria. Wie ein Schöpfrad, das sich immer weiter dreht.",
    "Kreislauf-Animation: blaue Figuren fahren hoch, kämpfen kurz, fahren zurück; Rad-Pfeil dreht sich über "
    "der Karte.",
    "Label „NORIA = SCHÖPFRAD“",
    "Rhythmischer Loop",
    "")
add("P32", 4,
    "Am Ende werden rund drei Viertel der gesamten französischen Armee durch Wer-döng gegangen sein.",
    "Balken-Grafik am Kartenrand füllt sich zu 3/4 blau.",
    "„≈ 3/4 DER FRANZ. ARMEE“",
    "",
    "")
add("P33", 4,
    "Einer von ihnen ist dieser Mann. Er hat keinen Namen. Er ist ein Soldat wie viele. Alles, was ihm passiert, "
    "ist so oder ähnlich Hunderttausenden passiert.",
    "Kamera zoomt ganz nah auf eine einzelne blaue Figur auf einer Ladefläche; Figur wird hervorgehoben "
    "(heller Ring, Rest leicht entsättigt).",
    "Einblender „EIN SOLDAT WIE VIELE“ (Markierung, die ihn bis Kap. 6 begleitet)",
    "Musik wird intim (Solo-Cello-artig)",
    "")
add("P34", 4,
    "Er sitzt auf der Ladefläche eines Lastwagens. Er hört die Front, lange bevor er sie sieht. Ob er von dieser "
    "Straße zurückkommt, wissen wir noch nicht.",
    "Der Lastwagen mit der Figur rollt nach Norden in den Rauch; Horizont blitzt orange.",
    "",
    "Fernes Grollen schwillt an → Schnitt",
    "")

# ---------------------------------------------------------------- 5 DIE HÖLLE
add("P35", 5,
    "Im März ändern die Deutschen ihren Plan. Ab dem sechsten März greifen sie auch am linken Maasufer an. "
    "Denn von dort schießt die französische Artillerie ihnen in die Flanke.",
    "Schwenk über die Maas nach Westen. Französische Geschütze am linken Ufer feuern quer über den Fluss. "
    "Neuer deutscher Angriffspfeil von Norden.",
    "Kapitelkarte „4 · DIE HÖLLE“; Zähler 06.03.1916 · TAG 15",
    "Musik M6 „Hölle“ (tief, dissonant, schwer)",
    "06.03.")
add("P36", 5,
    "Zwei Hügel bekommen Namen, die man nie mehr vergisst: Höhe dreihundertvier. Und der Tote Mann. Der Name ist älter als die Schlacht. Er klingt nur, als wäre er für sie erfunden worden.",
    "Zoom auf zwei Höhen (Relief tritt hervor), Höhen-Labels schweben ein.",
    "Labels „HÖHE 304“, „TOTER MANN (MORT-HOMME)“",
    "",
    "")
add("P37", 5,
    "Am zehnten April gibt Pe-täng einen Tagesbefehl heraus. Er endet mit Worten, die in Frankreich fast jeder kennt: "
    "Ku-rahsch! Ong lehs o-rah! Mut! Wir kriegen sie!",
    "Französische Figuren erheben sich kurz an der Linie.",
    "Zitat-Karte: „Courage ! On les aura !“ – Pétain, Tagesbefehl 10.04.1916 (Quelle unten eingeblendet)",
    "Kurzer Fanfaren-Akzent, sofort wieder Einschläge",
    "10.04.")
add("P38", 5,
    "Doch erst einmal kriegen die Deutschen die Hügel. Höhe dreihundertvier fällt Anfang Mai. Der Tote Mann Ende Mai. "
    "Drei Monate Kampf. Für zwei Hügel.",
    "Beide Höhen werden feldgrau; Frontlinie verschiebt sich nur minimal (Maßstab-Lineal zeigt ~2 km).",
    "Zähler läuft bis 29.05. TAG 99; Lineal-Einblendung",
    "Trockener Akzent auf „Für zwei Hügel“",
    "29.05.")
add("P39", 5,
    "Rechts der Maas rückt die Front auf das nächste Fort vor: Fort Woh. Am zweiten Juni stehen die Deutschen auf seinem Dach. Unten in den Gängen wird fast eine Woche gekämpft. Mit Handgranaten und Flammenwerfern. Im Dunkeln.",
    "Schwenk nach Osten zu Fort Vaux. Feldgraue Figuren auf dem Fort; Querschnitt-Grafik der Gänge "
    "(Vorlage aus Kap. 3) mit Flammen- und Blitz-Effekten.",
    "Orts-Label „FORT VAUX“; Zähler 02.06. TAG 103",
    "Dumpfe Explosionen unter Tage, Fauchen der Flammenwerfer",
    "02.06.")
add("P40", 5,
    "Kommandant Rä-nal schickt seine letzte Brieftaube los. Sie kommt an. Hilfe kommt trotzdem nicht durch. "
    "Am siebten Juni gibt Rä-nal auf. Nicht wegen der Deutschen. Wegen des Durstes.",
    "Weiße Taube fliegt vom Fort nach Verdun (Partikelspur). Blaue Entsatz-Pfeile prallen ab. "
    "Fort-Symbol wechselt auf Feldgrau. Wasser-Icon leert sich.",
    "Einblender „MAJOR SYLVAIN-EUGÈNE RAYNAL“; Zähler 07.06. TAG 108",
    "Flügelschlag, dann Stille",
    "07.06.")
add("P41", 5,
    "Inzwischen ist die Landschaft nicht mehr wiederzuerkennen. Die Wälder sind weg. Die Dörfer sind weg. "
    "Übrig ist ein Feld aus Trichtern. Trichter in Trichtern. Eine Mondlandschaft.",
    "Großer Überflug: Karte im Zerstörungsgrad 4 (Vergleich: kurz Split-Wipe mit dem Februar-Zustand).",
    "Wipe-Label „FEBRUAR“ | „JUNI“",
    "Wind über Ödland, fernes Dauerfeuer",
    "")
add("P42", 5,
    "Schätzungen zufolge fallen in zehn Monaten bis zu sechzig Millionen Granaten auf dieses Gebiet. Mehr als zwei pro Sekunde. Tag und Nacht.",
    "Einschläge im Takt von ~2/s übers ganze Bild, Trichter-Stempel vermehren sich.",
    "Zahl-Karte „BIS ZU 60.000.000 GRANATEN“ → „> 2 PRO SEKUNDE“ (Sekunden-Zeiger läuft)",
    "Metronom-artige Einschläge",
    "")
add("P43", 5,
    "Und mittendrin: unser Soldat. Er liegt nicht in einem Graben. Gräben gibt es hier kaum noch. Er liegt mit ein paar "
    "Kameraden in einem Granattrichter.",
    "Zoom auf die markierte blaue Figur in einem Trichter, drei weitere Figuren daneben.",
    "Markierung „EIN SOLDAT WIE VIELE“",
    "Musik leise, Atem, Erde rieselt",
    "")
add("P44", 5,
    "Essen und Wasser kommen nachts. Wenn überhaupt. Die Träger müssen durch dasselbe Feuer. Viele kommen nie an.",
    "Nacht-Overlay; kleine Träger-Figuren mit Kanistern schlängeln sich durchs Trichterfeld, zwei verschwinden in "
    "Einschlägen.",
    "",
    "Leuchtkugel-Zischen, Einschläge",
    "")
add("P45", 5,
    "Ende Juni hört er ein neues Geräusch. Granaten, die dumpfer aufschlagen. Grünkreuz. Gas. Über hunderttausend Gasgranaten fallen auf die Stellungen bei Flö-ri und Su-wil.",
    "Gelbgrüne Gaswolken quellen über Fleury und Souville und kriechen in die Senken (Code-Partikel). "
    "[KI-4, optional] „Gasangriff im Trichterfeld“ (4 s).",
    "Zähler 22.06. TAG 123; „GRÜNKREUZ (DIPHOSGEN) · > 100.000 GRANATEN“",
    "Dumpfe „Plopp“-Einschläge, Zischen, Gasglocke",
    "22.06.")
add("P46", 5,
    "Er reißt die Gasmaske hoch. Und wartet.",
    "Bild wird grünstichig und unscharf am Rand; die Figur im Trichter bekommt eine Maske.",
    "",
    "Gedämpfter Atem durch Maske, sonst Stille (2 s)",
    "")
add("P47", 5,
    "Am dreiundzwanzigsten Juni gibt General Ni-well, Pe-tängs Nachfolger, einen Tagesbefehl heraus. Daraus wird der Satz: Il nö pass-rong pa! Sie werden nicht durchkommen. Der genaue Wortlaut ist übrigens umstritten.",
    "Blaue Linie vor Souville verdickt sich.",
    "Zitat-Karte „Ils ne passeront pas !“ – nach Nivelle, Tagesbefehl 23.06.1916 + Badge „WORTLAUT UMSTRITTEN“",
    "Trommelwirbel",
    "23.06.")
add("P48", 5,
    "Das Dorf Flö-ri wechselt in diesem Sommer sechzehnmal den Besitzer. Sechzehnmal. Heute steht dort kein einziges "
    "Haus mehr.",
    "Fleury blinkt im Wechsel blau/feldgrau, 16 Ticks. Ruinen-Sprite bleibt übrig.",
    "Zähler „16 ×“ tickt hoch",
    "16 kurze Schläge, immer schneller",
    "")
add("P49", 5,
    "Am elften Juli kommt der letzte große Ansturm. Ziel: Fort Su-wil. Dahinter liegt nur noch Wer-döng. "
    "Rund dreißig Deutsche schaffen es bis auf das Fort. Die Stadt liegt keine fünf Kilometer entfernt.",
    "Massiver deutscher Pfeil auf Souville; eine kleine Gruppe Figuren erreicht das Fort-Symbol. Kamera zeigt "
    "Fort und Stadt in einem Bild, Lineal „< 5 KM“.",
    "Zähler 11.07. TAG 142; Orts-Label „FORT SOUVILLE“",
    "Musik steigert sich maximal",
    "11.07.")
add("P50", 5,
    "Ein letzter Stoß, und Wer-döng könnte fallen. Oder?",
    "Freeze: Figur auf dem Fort, Pfeilspitze zeigt auf die Stadt.",
    "",
    "Abbruch – 1 s Stille",
    "")

# ---------------------------------------------------------------- 6 DIE WENDE
add("P51", 6,
    "Die Rettung kommt nicht aus Wer-döng. Sie kommt von weit weg. Am ersten Juli hat an der Somme eine riesige "
    "britisch-französische Offensive begonnen. Auch, um Wer-döng zu entlasten.",
    "Riesiger Zoom-out bis Nordfrankreich (Inset-Karte), Somme-Pfeil leuchtet auf, Linie zieht sich zurück nach "
    "Verdun.",
    "Kapitelkarte „5 · DIE WENDE“; Label „SOMME · 01.07.1916“",
    "Musik M7 „Wende“ (Moll → Spannung löst sich)",
    "01.07.")
add("P52", 6,
    "Schon im Juni hat im Osten Russland angegriffen. Plötzlich braucht Deutschland seine Soldaten überall "
    "gleichzeitig. Geschütze und Divisionen rollen von Wer-döng ab.",
    "Feldgraue Geschütz- und Infanterie-Figuren verlassen die Verdun-Front Richtung Kartenrand (Westen/Osten).",
    "Pfeil-Labels „→ SOMME“, „→ OSTFRONT“",
    "Bahn, Rollgeräusche",
    "")
add("P53", 6,
    "Nach dem Fehlschlag am Fort Su-wil geht Falkenhayn hier zur Verteidigung über. Am neunundzwanzigsten August wird "
    "er abgesetzt. Der Mann, der Frankreich angeblich ausbluten lassen wollte, ist selbst am Ende. Politisch jedenfalls.",
    "Fragezeichen-Marker aus Kap. 2 blinkt über dem Hauptquartier. Falkenhayn-Medaillon kippt um.",
    "Zähler 29.08. TAG 191; Einblender „ABGESETZT · NACHFOLGER: HINDENBURG & LUDENDORFF“",
    "Trockener Akzent",
    "29.08.")
add("P54", 6,
    "Und unser Soldat? Er hat Glück. Seine Division wird abgelöst. No-ria. Er sitzt wieder auf einem Lastwagen. "
    "Diesmal in die andere Richtung. Viele aus seiner Kompanie sitzen nicht mehr mit drauf.",
    "Die markierte Figur auf einem Lastwagen Richtung Süden; Ladefläche halb leer (leere Plätze als "
    "Umrisse).",
    "Markierung „EIN SOLDAT WIE VIELE“ (letzter Auftritt)",
    "Musik sehr leise, Motor",
    "")
add("P55", 6,
    "Und ein paar hundert Meter gegenüber lag die ganze Zeit ein deutscher Soldat wie viele. Mit demselben Durst. "
    "Unter demselben Feuer.",
    "Kamera schwenkt über die Linie: eine feldgraue Figur in einem Trichter, gleiche Haltung, gespiegelt.",
    "",
    "Gleiches Motiv wie P43, gespiegelt",
    "")
add("P56", 6,
    "Im Herbst dreht Frankreich den Spieß um. Vierundzwanzigster Oktober. Tag zweihundertsiebenundvierzig. "
    "Dichter Nebel liegt über dem Plateau.",
    "Französische Geschützreihen wachsen; Karte versinkt in Nebel (Code-Nebel), nur Fort Douaumont sichtbar.",
    "Zähler 24.10. TAG 247",
    "Nebel-Atmo, dann französisches Trommelfeuer",
    "24.10.")
add("P57", 6,
    "Die französische Infanterie läuft direkt hinter einer Feuerwalze her. Ein Kolonialregiment aus Marokko stürmt "
    "Fort Du-o-mong. Nach wenigen Stunden ist es wieder französisch. Acht Monate, nachdem es fast kampflos verloren ging.",
    "Feuerwalze als wandernde Einschlagskante, blaue Figuren direkt dahinter. Fort-Symbol wird blau, Fahne wechselt.",
    "Groß: „DOUAUMONT ZURÜCKEROBERT“; Einblender „GENERAL MANGIN · RICM“",
    "Musik bricht durch (Dur-Akkord, kurz)",
    "")
add("P58", 6,
    "Am zweiten November räumen die Deutschen auch Fort Woh. Aber ein letzter Akt fehlt noch.",
    "Fort Vaux wird blau. Kamera hebt ab.",
    "Zähler 02.11. TAG 256",
    "Akkord hängt offen",
    "02.11.")

# ---------------------------------------------------------------- 7 FINALE
add("P59", 7,
    "Fünfzehnter Dezember. Tag zweihundertneunundneunzig. Ein letzter französischer Angriff. Die Dörfer Luw-mong und "
    "Be-song-woh fallen zurück an Frankreich. Über elftausend Deutsche gehen in Gefangenschaft.",
    "Winter-Grading, Schnee fällt wieder (Echo zum Anfang). Blaue Pfeile nach Norden, Front rückt vor.",
    "Kapitelkarte „6 · FINALE“; Zähler 15.12. TAG 299; „> 11.000 GEFANGENE“",
    "Musik M8 „Bilanz“ (ruhig, schwer)",
    "15.12.")
add("P60", 7,
    "Am achtzehnten Dezember ist es vorbei. Nach dreihundertzwei Tagen.",
    "Alle Effekte stoppen. Rauch zieht ab.",
    "Zähler 18.12.1916 · TAG 302 (bleibt stehen)",
    "Letzter Einschlag, Ausklingen, Wind",
    "18.12.")
add("P61", 7,
    "Und jetzt schau dir die Karte an. Hier verlief die Front im Februar. Und hier verläuft sie im Dezember. "
    "Ein paar Kilometer. Mehr nicht.",
    "Kamera fährt weit raus: Überblick. Februar-Linie (gestrichelt) und Dezember-Linie (durchgezogen) liegen "
    "fast übereinander; dazwischen ein schmaler Streifen Trichterwüste.",
    "Labels „21.02.1916“ / „18.12.1916“, Lineal mit „wenige km“",
    "Einzelner Klavierton",
    "")
add("P62", 7,
    "Dafür: rund dreihunderttausend Tote. Genaue Zahlen gibt es bis heute nicht. Gängige Schätzungen sprechen von etwa "
    "hundertsechzigtausend Franzosen und hundertvierzigtausend Deutschen.",
    "Der Streifen zwischen den Linien füllt sich mit winzigen Kreuz-Punkten (blau/grau).",
    "Zahl-Karte „≈ 300.000 TOTE“ (FR ≈ 162.000 · DE ≈ 143.000) + Badge „SCHÄTZUNG“",
    "",
    "")
add("P63", 7,
    "Das sind im Schnitt rund tausend Tote am Tag. Zehn Monate lang. Insgesamt so viele Menschen, wie heute in ganz "
    "Karlsruhe leben.",
    "Inset: Silhouette einer Großstadt füllt sich mit Punkten.",
    "„≈ 1.000 PRO TAG“ → „≈ EINWOHNER VON KARLSRUHE“",
    "",
    "")
add("P64", 7,
    "Neun Dörfer gibt es seitdem nicht mehr. Sie wurden nie wieder aufgebaut. Jedes hat bis heute einen Bürgermeister. Für einen Ort, an dem niemand wohnt.",
    "Neun Dorf-Ruinen leuchten nacheinander auf (Beaumont, Bezonvaux, Cumières, Douaumont, Fleury, Haumont, "
    "Louvemont, Ornes, Vaux).",
    "Neun Orts-Labels mit Zusatz „MORT POUR LA FRANCE“",
    "Neun leise Glockentöne",
    "")
add("P65", 7,
    "Also: Warum starben hier dreihunderttausend Menschen für ein paar Kilometer? Erstens: Vielleicht ging es nie um die Kilometer. Falkenhayn behauptete später, das Gelände sei nur der Köder gewesen.",
    "Leitfrage-Karte kehrt zurück. Dann: Fragezeichen-Marker aus Kap. 2 fliegt ins Bild.",
    "Frage-Karte (Design aus Hook); „1 · DER KÖDER“",
    "Musik nimmt Hook-Motiv auf",
    "")
add("P66", 7,
    "Ob er das wirklich so geplant oder sich nachträglich zurechtgelegt hat, wissen wir nicht. Das Dokument dazu ist nie aufgetaucht.",
    "Dokument-Symbol materialisiert halb und zerfällt wieder.",
    "Badge „UMSTRITTEN“",
    "",
    "")
add("P67", 7,
    "Zweitens: Keiner konnte aufhören. Für Frankreich wurde Wer-döng zum Symbol. Wer hier weicht, verliert mehr als eine Stadt. Und für Deutschland galt bald dasselbe. Zu viele Tote, um umzukehren.",
    "Zwei Waagschalen-Symbole über der Karte, beide sinken.",
    "„2 · DAS SYMBOL“",
    "",
    "")
add("P68", 7,
    "Drittens: Die Artillerie war stärker als jeder Plan. Wer angriff, lief in dasselbe Feuer, in das er den Gegner treiben wollte. Die Falle, wenn es eine war, schnappte für beide Seiten zu.",
    "Geschütze beider Seiten feuern gleichzeitig, Einschläge auf beiden Seiten der Linie.",
    "„3 · DIE FALLE“",
    "",
    "")
add("P69", 7,
    "Wer-döng war am Ende kein Kampf um Kilometer. Es war ein Kampf darum, wer zuerst aufgibt. Und keiner gab auf.",
    "Kamera steht still über der Linie (einziger ruhiger Moment, max. 5 s), dann sanfte Fahrt.",
    "Antwort-Karte (Design wie Frage-Karte): „KEIN KAMPF UM KILOMETER. EIN KAMPF DARUM, WER ZUERST AUFGIBT.“",
    "Musik-Höhepunkt, dann Abbau",
    "")
add("P70", 7,
    "Heute wächst über dem Schlachtfeld wieder Wald. Darunter liegen noch die Trichter. Im Beinhaus von Du-o-mong ruhen rund hundertdreißigtausend Unbekannte. Deutsche und Franzosen. Nebeneinander.",
    "Zeitsprung: Wald wächst über das Trichterfeld (Code-Animation), Beinhaus-Symbol bei Douaumont.",
    "Label „HEUTE“; „BEINHAUS VON DOUAUMONT · ~130.000 UNBEKANNTE“",
    "Vögel, Wind in Bäumen",
    "")
add("P71", 7,
    "Neunzehnhundertvierundachtzig standen hier ein deutscher Kanzler und ein französischer Präsident. "
    "Und reichten sich die Hand.",
    "Zwei Figuren (grau und blau) vor dem Beinhaus, Hände berühren sich (Code-Animation, keine Fotoimitation).",
    "„22.09.1984 · KOHL & MITTERRAND“",
    "Musik-Schlussakkord",
    "")

# ---------------------------------------------------------------- 8 OUTRO
add("P72", 8,
    "Wer-döng war nicht das Ende. An der Somme verlor die britische Armee an einem einzigen Tag fast sechzigtausend Mann, "
    "an Toten und Verwundeten. Wie das passieren konnte, zeigen wir im nächsten Video.",
    "Kamera fliegt nach Nordwesten von der Karte weg; neue Karte „SOMME“ blitzt als Teaser auf (Outro-Vorlage).",
    "Teaser-Karte „NÄCHSTES VIDEO: DIE SCHLACHT AN DER SOMME“",
    "Musik-Teaser (neues Motiv)",
    "")
add("P73", 8,
    "Wenn du das nicht verpassen willst: Abonniere War A Zett. Wir sehen uns an der Somme.",
    "Endcard: Abo-Button-Fläche + Platz für 2 Video-Vorschläge (YouTube-Endscreen-Zonen, 20 s).",
    "WarAZ-Logo-Schriftzug, „ABONNIEREN“",
    "Outro-Jingle",
    "")
