"""Sprechertext (Deutsch) – ein Eintrag pro Sprachaufnahme.

Zahlen und Jahreszahlen sind ausgeschrieben, damit die KI-Stimme sie sicher richtig spricht.
Panzertypen lautschriftnah („Mark Vier“, „A-sieben-V“). Die Zahlen auf dem Bildschirm stehen in scenes.py.
"""

SEGMENTS = [
    # ------------------------------------------------------------------ Luftaufnahme
    ("intro",
     "Die Somme bei Amiens, im Norden Frankreichs. Heute ziehen sich hier weite Getreidefelder über sanfte Hügel, "
     "dazwischen kleine Dörfer und stille Soldatenfriedhöfe. Im August neunzehnhundertachtzehn rollen über diese "
     "Felder Hunderte Panzer, und am Himmel kämpfen fast zweitausend Flugzeuge. In wenigen Stunden bricht die "
     "deutsche Front zusammen. Für die deutsche Armee wird es der schwärzeste Tag des Krieges, und der Anfang vom "
     "Ende des Ersten Weltkriegs."),

    # ------------------------------------------------------------------ 1 · Das letzte Spiel
    ("europa",
     "Anfang neunzehnhundertachtzehn tobt der Erste Weltkrieg im vierten Jahr. Auf der einen Seite stehen die "
     "Mittelmächte: das Deutsche Kaiserreich, Österreich-Ungarn, das Osmanische Reich und Bulgarien. Auf der anderen "
     "Seite die Alliierten: Frankreich, Großbritannien mit seinen Dominions, Italien und seit neunzehnhundertsiebzehn "
     "auch die Vereinigten Staaten. Russland dagegen ist nach der Revolution aus dem Krieg ausgeschieden. Im März "
     "unterzeichnet es den Frieden von Brest-Litowsk."),

    ("ludendorff",
     "Für die deutsche Oberste Heeresleitung unter Erich Ludendorff ist das die letzte Chance. Dutzende Divisionen "
     "werden von der Ostfront in den Westen verlegt. Zum ersten Mal seit Jahren sind die Deutschen dort zahlenmäßig "
     "überlegen. Doch die Zeit läuft gegen sie. Monat für Monat landen Hunderttausende amerikanische Soldaten in "
     "Frankreich. Ludendorff will den Krieg entscheiden, bevor die Amerikaner in voller Stärke an der Front stehen."),

    ("michael",
     "Am einundzwanzigsten März neunzehnhundertachtzehn beginnt die deutsche Frühjahrsoffensive, das Unternehmen "
     "Michael. Mehr als sechstausend Geschütze eröffnen im Morgennebel das Feuer. Dann stürmen besonders "
     "ausgebildete Stoßtrupps vor, umgehen die feindlichen Stützpunkte und dringen tief in das Hinterland ein. Die "
     "britische Front an der Somme bricht auf rund siebzig Kilometern Breite ein. Zum ersten Mal seit "
     "neunzehnhundertvierzehn ist der Krieg im Westen wieder in Bewegung."),

    ("amiens_ziel",
     "In zwei Wochen rücken die Deutschen bis zu sechzig Kilometer vor. Ihr Ziel ist Amiens, der wichtigste "
     "Eisenbahnknoten hinter der alliierten Front. Fällt die Stadt, sind Briten und Franzosen voneinander getrennt. "
     "In höchster Not stellen die Alliierten ihre Armeen unter einen gemeinsamen Oberbefehlshaber, den französischen "
     "General Ferdinand Foch. Vor dem Städtchen Villers-Bretonneux, rund fünfzehn Kilometer vor Amiens, kommt der "
     "Angriff Anfang April zum Stehen."),

    ("verluste_michael",
     "Der Preis ist gewaltig. Bis Anfang April verlieren die Deutschen rund zweihundertvierzigtausend Mann, darunter "
     "viele ihrer besten Stoßtruppen. Briten und Franzosen verlieren zusammen etwa zweihundertfünfzigtausend. "
     "Ludendorff greift nun an anderen Stellen an: in Flandern, dann an der Aisne und an der Marne. Jedes Mal "
     "gewinnen die Deutschen Gelände, doch nirgends gelingt der entscheidende Durchbruch. Ihre Kräfte schwinden."),

    ("luftkrieg",
     "Auch der Himmel über der Somme ist umkämpft. Am ersten April neunzehnhundertachtzehn entsteht die Royal Air "
     "Force, die erste eigenständige Luftwaffe der Welt. Jagdflieger beider Seiten liefern sich täglich Luftkämpfe "
     "über den Gräben. Am einundzwanzigsten April wird hier der berühmteste Jagdflieger des Krieges abgeschossen: "
     "Manfred von Richthofen, der Rote Baron. Er stürzt bei Vaux-sur-Somme ab, mitten über den australischen "
     "Stellungen."),

    # ------------------------------------------------------------------ 2 · Stahl gegen Stahl
    ("vb_angriff",
     "Am vierundzwanzigsten April greifen die Deutschen Villers-Bretonneux erneut an. Diesmal mit einer neuen Waffe: "
     "dem Sturmpanzerwagen A-sieben-V. Mehr als ein Dutzend dieser schweren deutschen Panzer rollt im Nebel und unter "
     "Gasbeschuss auf die britischen Linien zu. Die Verteidiger weichen zurück, und die Deutschen nehmen das "
     "Städtchen ein. Amiens liegt nun in Reichweite der deutschen Geschütze."),

    ("panzerduell",
     "Dann kommt es zu einer Begegnung, die es so noch nie gegeben hat. Drei britische Panzer vom Typ Mark Vier "
     "stoßen auf drei deutsche A-sieben-V. Zum ersten Mal in der Geschichte kämpft Panzer gegen Panzer. Leutnant "
     "Frank Mitchell lässt seinen Mark Vier anhalten, damit der Richtschütze genau zielen kann. Mehrere Treffer "
     "setzen den deutschen Panzer Nixe außer Gefecht. Später greifen sieben schnelle britische Whippets die "
     "deutsche Infanterie an."),

    ("anzac",
     "In der Nacht zum fünfundzwanzigsten April schlagen zwei australische Brigaden zurück. Ohne Artillerievorbereitung "
     "umfassen sie Villers-Bretonneux von Norden und von Süden. Am Morgen ist das Städtchen wieder in alliierter "
     "Hand, genau am Anzac Day, drei Jahre nach der Landung bei Gallipoli. Amiens ist gerettet. Bis heute erinnert "
     "in der Schule von Villers-Bretonneux die Inschrift „Vergessen wir Australien nie“ an diese Nacht."),

    ("hamel",
     "Am vierten Juli erprobt der australische General John Monash bei Le Hamel eine neue Art des Angriffs. "
     "Infanterie, Artillerie, Panzer und Flugzeuge arbeiten nach einem genauen Zeitplan zusammen. Rund sechzig neue "
     "Panzer vom Typ Mark Fünf rollen mit der Infanterie vor, Flugzeuge werfen Munition an Fallschirmen ab. Mit dabei "
     "sind zum ersten Mal amerikanische Soldaten. Nach nur dreiundneunzig Minuten ist alles vorbei. Le Hamel wird "
     "zur Blaupause für Amiens."),

    ("marne",
     "Mitte Juli wagt Ludendorff an der Marne seinen letzten großen Angriff. Er scheitert. Am achtzehnten Juli "
     "schlagen Franzosen und Amerikaner mit Hunderten Panzern zurück. Die Initiative geht endgültig auf die "
     "Alliierten über. Foch, bald darauf zum Marschall von Frankreich ernannt, will nun an der ganzen Front "
     "angreifen. Der erste große Schlag soll vor Amiens fallen."),

    # ------------------------------------------------------------------ 3 · Der Plan
    ("plan",
     "Den Plan entwirft der britische General Henry Rawlinson, Befehlshaber der vierten Armee. Auf rund zwanzig "
     "Kilometern Breite zwischen der Somme und dem Flüsschen Luce sollen drei Korps angreifen: nördlich der Somme das "
     "britische dritte Korps, in der Mitte die Australier unter Monash, im Süden die Kanadier unter Arthur Currie. "
     "Südlich davon schließt sich die französische erste Armee unter General Debeney an."),

    ("geheim",
     "Alles hängt an der Überraschung. Das gesamte kanadische Korps, über hunderttausend Mann, wird nachts und im "
     "Geheimen rund siebzig Kilometer aus der Gegend von Arras herangeführt. Zur Täuschung bleiben zwei kanadische "
     "Bataillone und Funkstationen in Flandern zurück und täuschen dort einen Angriff vor. In die Soldbücher wird ein "
     "Zettel geklebt: Halt den Mund! Und es gibt keinen tagelangen Beschuss vorher. Die Geschütze schießen sich "
     "nicht einmal ein."),

    ("aufmarsch",
     "Hinter der Front sammeln sich gewaltige Kräfte: über zweitausend Geschütze, rund dreihundertvierzig schwere "
     "Panzer vom Typ Mark Fünf, zweiundsiebzig schnelle Whippets und hundertzwanzig Versorgungspanzer. Am Himmel "
     "stehen rund achthundert britische und elfhundert französische Flugzeuge bereit, gegenüber nur etwa "
     "dreihundertfünfundsechzig deutschen. In der Nacht zum achten August rollen die Panzer an die Front. Tief "
     "fliegende Flugzeuge übertönen das Dröhnen ihrer Motoren."),

    # ------------------------------------------------------------------ 4 · 8. August 1918
    ("angriff",
     "Achter August neunzehnhundertachtzehn, vier Uhr zwanzig am Morgen. Dichter Nebel liegt über den Feldern. "
     "Schlagartig eröffnen über zweitausend Geschütze das Feuer. Eine Feuerwalze legt sich vor die angreifende "
     "Infanterie und wandert Schritt für Schritt nach vorne. Dahinter rollen die Panzer aus dem Nebel. Die deutschen "
     "Verteidiger werden völlig überrascht. Viele ihrer Batterien werden getroffen, bevor sie überhaupt antworten "
     "können."),

    ("kanadier",
     "Im Süden stürmen die Kanadier durch das Tal der Luce. Hangard, Demuin und Beaucourt fallen in rascher Folge. "
     "Panzer brechen Maschinengewehrnester auf, die die Infanterie im Nebel kaum erkennen kann. Am Nachmittag "
     "rücken sogar Kavallerie und Whippets vor. Bis zum Abend dringen die Kanadier rund dreizehn Kilometer tief in "
     "die deutschen Linien ein. So weit ist an der Westfront seit Jahren niemand an einem einzigen Tag vorgestoßen."),

    ("australier",
     "In der Mitte gehen die Australier in Wellen vor. Sobald eine Division ihr Ziel erreicht hat, überholt die "
     "nächste sie und greift weiter an. Warfusée, Bayonvillers und Harbonnières werden genommen. Die Australier "
     "erbeuten ganze Batterien und sogar ein riesiges deutsches Eisenbahngeschütz. Am Ende des Tages stehen sie "
     "rund elf Kilometer weiter östlich, fast alle Ziele sind erreicht."),

    ("musical_box",
     "Eine Geschichte dieses Tages wird berühmt. Der Whippet Musical Box unter Leutnant Clement Arnold verliert den "
     "Anschluss und fährt allein tief hinter die deutschen Linien. Rund neun Stunden lang greift die dreiköpfige "
     "Besatzung Batterien, Lager und Kolonnen an. Am Ende wird der Panzer von Granaten getroffen und gerät in Brand. "
     "Ein Besatzungsmitglied fällt, die beiden anderen geraten in Gefangenschaft."),

    ("luftschlacht",
     "Über dem Schlachtfeld tobt eine der größten Luftschlachten des Krieges. Britische Jagdflugzeuge greifen im "
     "Tiefflug Kolonnen und Geschütze an. Am Nachmittag sollen Bomber die Brücken über die Somme zerstören, um den "
     "deutschen Rückzug abzuschneiden. Doch deutsche Jagdgeschwader eilen herbei. Die Brücken bleiben fast alle "
     "stehen, und die Royal Air Force verliert an diesem einen Tag fast hundert Maschinen, abgeschossen oder schwer "
     "beschädigt."),

    ("chipilly",
     "Nicht überall läuft es so gut. Nördlich der Somme bleibt das britische dritte Korps am Chipilly-Rücken stecken, "
     "einer steilen, bewaldeten Höhe über dem Fluss. Von dort beschießen deutsche Maschinengewehre die Australier am "
     "anderen Ufer. Im Süden greifen die Franzosen erst nach einer kurzen Artillerievorbereitung an. Ohne Panzer "
     "kommen sie langsamer voran, doch auch sie gewinnen mehrere Kilometer."),

    ("schwarzer_tag",
     "Am Abend des achten August ist die deutsche Front auf über zwanzig Kilometern Breite zerbrochen. Die Deutschen "
     "verlieren an einem einzigen Tag rund siebenundzwanzigtausend Mann, darunter mehr als zwölftausend Gefangene, "
     "und rund vierhundert Geschütze. Ganze Einheiten haben sich ergeben. Erich Ludendorff nennt den achten August "
     "später den schwarzen Tag des deutschen Heeres."),

    # ------------------------------------------------------------------ 5 · Die Tage danach
    ("tag9",
     "Am neunten August geht der Angriff weiter, doch die Überraschung ist vorbei. Die Deutschen führen Reserven "
     "heran, und die Angriffe der Alliierten sind schlechter abgestimmt. Nördlich der Somme stürmen amerikanische "
     "Soldaten der dreiunddreißigsten Division zusammen mit Briten den Chipilly-Rücken. Von den Panzern sind viele "
     "ausgefallen: abgeschossen, liegengeblieben, oder die Besatzungen sind völlig erschöpft."),

    ("tag10",
     "Am zehnten August rücken die Franzosen in Montdidier ein. Die Deutschen haben die Stadt geräumt, um nicht "
     "eingeschlossen zu werden. Auch Briten, Australier und Kanadier stoßen weiter vor, aber immer langsamer. Sie "
     "erreichen nun das alte Schlachtfeld von neunzehnhundertsechzehn: eine Landschaft voller Trichter, verfallener "
     "Gräben und rostigem Stacheldraht, in der die Panzer kaum noch vorankommen."),

    ("tag11",
     "Am elften August stockt der Vormarsch. Der deutsche Widerstand wird stärker, und von den über vierhundert "
     "Kampfpanzern des ersten Tages sind nur noch wenige Dutzend einsatzbereit. Statt sich festzurennen, lässt "
     "Feldmarschall Douglas Haig den Angriff bei Amiens einstellen und an anderer Stelle neu ansetzen. Auf deutscher "
     "Seite soll Kaiser Wilhelm der Zweite gesagt haben: Wir sind an der Grenze unserer Leistungsfähigkeit. Der Krieg "
     "muss beendet werden."),

    ("bilanz_amiens",
     "Die Schlacht von Amiens dauert nur vier Tage. Die Alliierten rücken bis zu zwanzig Kilometer vor. Sie verlieren "
     "rund sechsundvierzigtausend Mann, etwa zur Hälfte Briten mit ihren Dominions und zur Hälfte Franzosen. Die "
     "Deutschen verlieren rund fünfundsiebzigtausend Mann, darunter fast dreißigtausend Gefangene. Wichtiger als das "
     "gewonnene Gelände ist aber etwas anderes: Die deutsche Armee hat den Glauben an den Sieg verloren."),

    # ------------------------------------------------------------------ 6 · Hundert Tage
    ("hundert",
     "Amiens ist der Beginn der Hunderttageoffensive. Foch lässt nun an immer neuen Stellen angreifen, bei Albert, "
     "bei Arras, an der Aisne und in den Argonnen. Die Deutschen müssen Schritt für Schritt zurückweichen, bis in "
     "ihre stärkste Verteidigungslinie, die Siegfriedstellung, von den Alliierten Hindenburg-Linie genannt."),

    ("hindenburg",
     "Ende September greifen Briten, Australier und Amerikaner die Siegfriedstellung am Kanal von Saint-Quentin an. "
     "Am neunundzwanzigsten September brechen sie durch. Am selben Tag erklärt Ludendorff, der Krieg sei militärisch "
     "nicht mehr zu gewinnen, und verlangt ein sofortiges Waffenstillstandsangebot. Wenige Tage später bittet die "
     "neue deutsche Regierung den amerikanischen Präsidenten Woodrow Wilson um Frieden."),

    ("zusammenbruch",
     "Im Herbst brechen die Verbündeten Deutschlands zusammen. Bulgarien gibt Ende September auf, das Osmanische "
     "Reich Ende Oktober, Österreich-Ungarn Anfang November. Ludendorff wird entlassen. In Kiel meutern die Matrosen "
     "der Flotte, die Revolution erfasst ganz Deutschland. Am neunten November wird die Abdankung des Kaisers "
     "verkündet, und in Berlin wird die Republik ausgerufen."),

    ("waffenstillstand",
     "Im Wald von Compiègne unterzeichnen deutsche Unterhändler in einem Eisenbahnwagen des Marschalls Foch den "
     "Waffenstillstand. Am elften November neunzehnhundertachtzehn um elf Uhr vormittags schweigen an der Westfront "
     "die Waffen. Nach mehr als vier Jahren ist der Erste Weltkrieg zu Ende. Rund siebzehn Millionen Menschen sind "
     "tot, Soldaten und Zivilisten."),

    # ------------------------------------------------------------------ 7 · Erbe
    ("erbe",
     "Amiens verändert die Kriegsführung. Zum ersten Mal greifen Infanterie, Artillerie, Panzer und Flugzeuge in "
     "großem Maßstab nach einem gemeinsamen Plan an. Was hier erprobt wird, prägt die Kriege des zwanzigsten "
     "Jahrhunderts. Heute ist die Landschaft wieder friedlich. Nur die Friedhöfe und Denkmäler der Australier, "
     "Kanadier, Briten, Franzosen und Deutschen erinnern an die Kämpfe von neunzehnhundertachtzehn."),

    ("gedenken",
     "Am achten August zweitausendachtzehn, genau hundert Jahre nach dem Angriff, versammeln sich in der Kathedrale "
     "von Amiens Nachfahren der Soldaten aus Großbritannien, Australien, Kanada, Frankreich und den Vereinigten "
     "Staaten. Unter den Gästen ist auch der frühere deutsche Bundespräsident Joachim Gauck. Gemeinsam gedenken sie "
     "der Toten. Amiens, neunzehnhundertachtzehn. Im Gedenken an alle Gefallenen beider Seiten."),
]
