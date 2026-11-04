"""Sprechertext (Deutsch) – ein Eintrag pro Sprachaufnahme.

Zahlen und Jahreszahlen sind ausgeschrieben, damit die KI-Stimme sie sicher richtig spricht.
Französische Namen spricht die Stimme (ElevenLabs v4, „Alistair“) französisch aus (Aussprachetest vom 4.11.2026).
Die Zahlen auf dem Bildschirm stehen in scenes.py.
"""

SEGMENTS = [
    ("intro",
     "Verdun, an der Maas im Nordosten Frankreichs. Heute bedecken dichte Wälder die Hügel nördlich der Stadt. "
     "Doch unter den Bäumen liegt eine zerrissene Landschaft: Trichter an Trichter, eingestürzte Gräben, "
     "verschwundene Dörfer. Im Jahr neunzehnhundertsechzehn kämpfen hier Deutsche und Franzosen dreihundert Tage "
     "lang um wenige Kilometer Boden. Es wird die längste Schlacht des Ersten Weltkriegs. Am Ende stehen rund "
     "dreihunderttausend Tote, und ein Name, der bis heute für das Grauen des Krieges steht."),

    ("europa",
     "Sommer neunzehnhundertvierzehn. In Europa beginnt der Erste Weltkrieg. Auf der einen Seite stehen die "
     "Mittelmächte: das Deutsche Kaiserreich und Österreich-Ungarn, bald auch das Osmanische Reich und Bulgarien. "
     "Auf der anderen Seite die Entente: Frankreich, Großbritannien und das Russische Zarenreich. Deutschland setzt "
     "alles auf einen schnellen Sieg im Westen. Seine Armeen marschieren durch Belgien nach Frankreich, bis kurz "
     "vor Paris."),

    ("westfront",
     "Doch an der Marne wird der deutsche Vormarsch im September gestoppt. Beide Seiten graben sich ein. Bald zieht "
     "sich eine durchgehende Linie aus Schützengräben von der Nordseeküste in Belgien bis an die Grenze der "
     "Schweiz: die Westfront. Neunzehnhundertfünfzehn rennen Franzosen und Briten immer wieder gegen die deutschen "
     "Stellungen an. Hunderttausende fallen, doch die Front bewegt sich kaum."),

    ("falkenhayn",
     "Ende neunzehnhundertfünfzehn sucht der deutsche Generalstabschef Erich von Falkenhayn einen Ausweg. Er will "
     "einen Ort angreifen, den Frankreich niemals aufgeben kann. Dort soll sich die französische Armee im "
     "Abwehrkampf verbluten. So hat es Falkenhayn jedenfalls nach dem Krieg in seinen Erinnerungen beschrieben, "
     "ein Original dieser berühmten Denkschrift wurde nie gefunden. Sein Ziel aber ist klar: Verdun."),

    ("festung",
     "Verdun ist seit Jahrhunderten eine Festungsstadt. Ein Ring aus neunzehn großen Forts und Dutzenden kleineren "
     "Werken umgibt die Stadt. Das stärkste von ihnen ist Fort Douaumont. Doch die französische Führung hält die "
     "Forts inzwischen für veraltet. Deutsche Riesengeschütze hatten neunzehnhundertvierzehn die belgischen "
     "Festungen von Lüttich und Namur in wenigen Tagen zerschlagen. Also werden neunzehnhundertfünfzehn die meisten "
     "Geschütze aus den Forts von Verdun abgezogen."),

    ("frontbogen",
     "Verdun liegt in einem Frontbogen, der weit in die deutschen Linien hineinragt. Im Norden und Osten stehen die "
     "Deutschen nur wenige Kilometer vor den Forts. Die wichtigen Bahnlinien in die Stadt sind unterbrochen oder "
     "liegen unter deutschem Beschuss. Nach Süden bleiben nur eine Landstraße und eine schmale Kleinbahn. Für die "
     "Verteidiger eine gefährliche Lage. Für die Angreifer eine verlockende."),

    ("gericht",
     "Im Januar neunzehnhundertsechzehn beginnen die Vorbereitungen für das Unternehmen Gericht. Die deutsche fünfte "
     "Armee unter Kronprinz Wilhelm zieht mehr als zwölfhundert Geschütze zusammen, darunter gewaltige Mörser mit "
     "zweiundvierzig Zentimetern Kaliber. Neun Divisionen stehen für den ersten Angriff bereit. Losgehen soll es am "
     "zwölften Februar. Doch Regen, Schnee und Nebel verzögern den Angriff um neun Tage. Zeit, in der die Franzosen "
     "ihre Linien eilig verstärken."),

    ("trommelfeuer",
     "Am frühen Morgen des einundzwanzigsten Februar neunzehnhundertsechzehn bricht das Inferno los. Auf einer Front "
     "von rund vierzig Kilometern feuern die deutschen Geschütze ohne Pause. Stundenlang schlagen Granaten in die "
     "französischen Gräben, Wälder und Dörfer ein. Allein am ersten Tag sollen es rund eine Million gewesen sein. "
     "Am Nachmittag gehen die ersten deutschen Stoßtrupps vor."),

    ("caures",
     "Im Bois des Caures, einem Wald nördlich von Verdun, halten rund zwölfhundert französische Jäger unter "
     "Oberstleutnant Émile Driant die vorderste Linie. Der Wald wird förmlich umgepflügt. Doch als die Deutschen "
     "angreifen, schlagen ihnen aus Trichtern und zerschossenen Unterständen Schüsse entgegen. Zwei Tage lang halten "
     "die Jäger stand. Dann fällt Driant. Von seinen zwölfhundert Männern kommen nur wenig mehr als hundert zurück."),

    ("vormarsch",
     "Trotzdem rücken die Deutschen Tag für Tag vor. Haumont fällt, dann Samogneux und Beaumont. Die erste und die "
     "zweite französische Stellung brechen zusammen. Tausende Franzosen geraten in Gefangenschaft, ganze Einheiten "
     "werden aufgerieben. Auch im Osten, in der Ebene der Woëvre, ziehen sich die Franzosen an den Fuß der Höhen "
     "zurück. Der Weg nach Verdun scheint offen."),

    ("douaumont",
     "Am fünfundzwanzigsten Februar geschieht das Unglaubliche. Fort Douaumont, das stärkste Fort von Verdun, ist "
     "nur noch mit einer Handvoll älterer Soldaten besetzt. Ein kleiner Trupp des brandenburgischen "
     "Infanterie-Regiments Nummer vierundzwanzig klettert in den Graben, dringt durch eine unbewachte Öffnung ein und "
     "nimmt die überraschte Besatzung gefangen, ohne einen einzigen Schuss. In Deutschland wird der Sieg gefeiert. "
     "In Frankreich ist der Schock gewaltig."),

    ("petain",
     "Noch am selben Tag erhält General Philippe Pétain den Befehl über die Verteidigung von Verdun. Er schlägt sein "
     "Hauptquartier im Dorf Souilly auf, südlich der Stadt. Pétain ordnet die Artillerie neu, lässt Stellungen "
     "ausbauen und verlangt, dass kein Meter Boden mehr kampflos aufgegeben wird. Vor allem aber erkennt er: Diese "
     "Schlacht wird über den Nachschub entschieden."),

    ("voie_sacree",
     "Von Bar-le-Duc führt eine einzige Landstraße nach Verdun. Auf ihr rollt nun Tag und Nacht ein endloser Strom "
     "aus Lastwagen. Zu Spitzenzeiten fährt alle vierzehn Sekunden ein Fahrzeug. Im Durchschnitt bringen sie jeden "
     "Tag rund dreizehntausend Soldaten und fast achttausend Tonnen Material und Munition an die Front. Arbeiter "
     "schaufeln ununterbrochen Schotter auf die Fahrbahn, damit sie nicht wegbricht. Später nennen die Franzosen "
     "diese Straße die Voie Sacrée, den heiligen Weg."),

    ("noria",
     "Pétain lässt seine Divisionen nicht bis zur Vernichtung kämpfen. Nach einigen Tagen oder Wochen werden sie "
     "abgelöst und durch frische Truppen ersetzt. Die Franzosen nennen dieses System Noria, nach dem Schöpfrad. So "
     "kämpfen bis Ende des Jahres rund drei Viertel der gesamten französischen Armee bei Verdun. Für fast jede "
     "französische Familie wird Verdun zur Schlacht ihrer Söhne, Väter und Brüder."),

    ("linkes_ufer",
     "Vom westlichen Ufer der Maas aus feuert die französische Artillerie in die Flanke der Angreifer. Deshalb "
     "greifen die Deutschen ab dem sechsten März auch dort an. Ihre Ziele sind zwei kahle Hügel: der Tote Mann und "
     "die Höhe dreihundertvier. Wochenlang wird um jeden Meter gekämpft, Angriff folgt auf Gegenangriff. Erst Anfang "
     "Mai fällt die Höhe dreihundertvier, Ende Mai auch der Tote Mann."),

    ("hoelle",
     "Die Landschaft um Verdun wird in wenigen Monaten vollständig zerstört. Wälder verschwinden, Dörfer zerfallen zu "
     "Staub, Trichter reiht sich an Trichter. Die Soldaten liegen tagelang in Schlamm und Kälte zwischen den Toten, "
     "oft ohne Wasser und ohne warmes Essen. Viele werden nie gefunden. Die Männer beider Seiten nennen Verdun bald "
     "nur noch die Hölle, die Knochenmühle, die Blutpumpe."),

    ("mai",
     "Im April schließt Pétain einen Tagesbefehl mit dem Satz: Courage, on les aura. Nur Mut, wir kriegen sie. "
     "Anfang Mai wird er befördert, General Robert Nivelle übernimmt das Kommando bei Verdun. Nivelle will angreifen. "
     "Am zweiundzwanzigsten Mai stürmen französische Truppen unter General Charles Mangin gegen Fort Douaumont. Sie "
     "erreichen das Fort, werden aber nach zwei Tagen wieder zurückgeworfen."),

    ("vaux",
     "Anfang Juni wenden sich die Deutschen gegen Fort Vaux, östlich von Douaumont. Am ersten Juni erreichen sie das "
     "Fort. Im Inneren drängen sich rund sechshundert Mann, darunter viele Verwundete und Versprengte, obwohl das "
     "Fort nur für etwa zweihundertfünfzig gebaut ist. Die Deutschen kämpfen sich mit Handgranaten und "
     "Flammenwerfern durch die dunklen Gänge vor. Die Franzosen verteidigen jeden Meter hinter Barrikaden aus "
     "Sandsäcken."),

    ("raynal",
     "Das größte Problem ist das Wasser. Die Zisterne ist fast leer, jeder Mann bekommt nur noch wenige Schlucke am "
     "Tag. Am vierten Juni lässt Kommandant Sylvain Raynal seine letzte Brieftaube fliegen, Le Vaillant. Ihre "
     "Botschaft: Wir halten noch, aber wir brauchen dringend Entsatz. Die Taube erreicht Verdun, doch Hilfe kommt "
     "nicht. Am siebten Juni ergibt sich Raynal. Die Deutschen erweisen der Besatzung militärische Ehren."),

    ("gas",
     "Nach Vaux soll der letzte große Stoß folgen. In der Nacht zum dreiundzwanzigsten Juni feuern die Deutschen "
     "mehr als hunderttausend Granaten mit einem neuen Giftgas auf die französischen Batterien: Grünkreuz, ein Kampfstoff auf Phosgenbasis, der die Lunge zerstört. Die "
     "französischen Gasmasken bieten kaum Schutz, viele Geschütze verstummen. Am Morgen greifen die Deutschen auf "
     "breiter Front an."),

    ("fleury",
     "Sie erobern das Werk Thiaumont und dringen in das Dorf Fleury ein. Nur noch wenige Kilometer trennen sie von "
     "Verdun. Es ist der gefährlichste Moment der Schlacht. General Nivelle schließt seinen Tagesbefehl mit den "
     "Worten: Ils ne passeront pas. Sie werden nicht durchkommen. Um Fleury wird wochenlang gerungen. Bis August "
     "wechselt das Dorf sechzehn Mal den Besitzer, bis von ihm nichts mehr übrig ist."),

    ("somme",
     "Doch an den anderen Fronten ändert sich die Lage. Im Osten beginnt Anfang Juni die große russische Offensive "
     "unter General Brussilow. Und am ersten Juli greifen Briten und Franzosen an der Somme an. Die deutsche "
     "Heeresleitung muss Truppen, Geschütze und Flugzeuge von Verdun abziehen. Der Angriff auf Verdun verliert an Kraft. An der Somme beginnt die nächste Materialschlacht, noch größer als Verdun."),

    ("souville",
     "Am elften Juli wagen die Deutschen einen letzten Versuch. Wieder mit Gas greifen sie Fort Souville an, das "
     "letzte große Fort vor der Stadt. Am Morgen des zwölften Juli erreicht ein kleiner Trupp sogar das Dach des "
     "Forts. Von hier sind es keine fünf Kilometer mehr bis Verdun. Doch französische Gegenangriffe werfen die "
     "Männer zurück. Weiter kommen die Deutschen nie."),

    ("wende",
     "Ende August wird Falkenhayn als Generalstabschef abgelöst. Paul von Hindenburg und Erich Ludendorff übernehmen "
     "die Oberste Heeresleitung. Anfang September stellen die Deutschen ihre Angriffe bei Verdun ein. Die Schlacht, "
     "die Frankreich ausbluten sollte, hat auch die deutsche Armee furchtbar geschwächt. Nun bereiten die Franzosen "
     "ihre Antwort vor."),

    ("vorbereitung",
     "Nivelle und Mangin planen den Gegenschlag. Eine gewaltige Artillerie wird zusammengezogen, darunter zwei "
     "riesige Eisenbahngeschütze mit vierzig Zentimetern Kaliber. Ab dem dreiundzwanzigsten Oktober schlagen ihre "
     "Granaten in Fort Douaumont ein. Mehrere durchschlagen die meterdicke Decke aus Beton. Die deutsche Besatzung "
     "muss große Teile des Forts räumen."),

    ("douaumont_zurueck",
     "Am vierundzwanzigsten Oktober greifen drei französische Divisionen im dichten Nebel an. Vor ihnen her wandert "
     "eine Feuerwalze, ein Vorhang aus Granaten, dem die Infanterie dicht folgt. Kolonialtruppen aus Marokko, "
     "Somalia und dem Senegal stürmen die Höhe. Noch am selben Tag ist Fort Douaumont wieder in französischer Hand. "
     "Rund sechstausend deutsche Soldaten geraten in Gefangenschaft."),

    ("vaux_zurueck",
     "Am zweiten November räumen die Deutschen auch Fort Vaux, die Franzosen ziehen kampflos ein. Über dem Fort weht wieder die Trikolore. In wenigen Tagen "
     "haben sie zurückgewonnen, wofür die Deutschen Monate gekämpft und Zehntausende Männer verloren hatten."),

    ("dezember",
     "Mitte Dezember folgt der letzte Schlag. Vom fünfzehnten bis zum achtzehnten Dezember drängen die Franzosen die "
     "Deutschen um mehrere Kilometer zurück und erobern Louvemont und Bezonvaux. Sie nehmen rund elftausend "
     "Gefangene und erbeuten hundertfünfzehn Geschütze. Am achtzehnten Dezember neunzehnhundertsechzehn endet die "
     "Schlacht um Verdun. Östlich der Maas verläuft die Front nun fast wieder dort, wo sie im Februar begonnen "
     "hatte."),

    ("bilanz",
     "Rund dreihundert Tage hat die Schlacht gedauert. Die Verluste sind kaum vorstellbar. Frankreich verliert rund "
     "dreihundertsiebenundsiebzigtausend Mann an Toten, Verwundeten und Vermissten, Deutschland rund "
     "dreihundertsiebenunddreißigtausend. Zusammen mehr als siebenhunderttausend. Etwa dreihunderttausend Soldaten "
     "sind tot. Im Durchschnitt fast tausend an jedem einzelnen Tag. Kaum eine andere Schlacht hat auf so engem Raum so viele "
     "Menschenleben gefordert."),

    ("landschaft",
     "Neun Dörfer sind von der Landkarte verschwunden. Die meisten wurden nie wieder aufgebaut. Bis heute gelten sie "
     "als für Frankreich gestorben, und doch hat jedes von ihnen noch einen Bürgermeister. Der Boden ist so voller "
     "Blindgänger, Gift und Gebeine, dass man ihn nach dem Krieg aufforstet. Der Wald von Verdun wächst auf einem "
     "Schlachtfeld."),

    ("erbe",
     "Auf der Höhe bei Douaumont steht heute das Beinhaus. In ihm ruhen die Gebeine von rund hundertdreißigtausend "
     "Soldaten, die nie identifiziert werden konnten, Franzosen und Deutsche. Davor liegen rund sechzehntausend "
     "französische Gräber. Für Frankreich wird Verdun zum Symbol des Durchhaltens, für Deutschland zum Symbol eines "
     "sinnlosen Opfers. Für beide ist es eine Schlacht, die man nie vergessen darf."),

    ("gedenken",
     "Am zweiundzwanzigsten September neunzehnhundertvierundachtzig stehen hier, vor dem Beinhaus von Douaumont, der "
     "französische Präsident François Mitterrand und der deutsche Bundeskanzler Helmut Kohl. Während die Hymnen "
     "erklingen, reichen sie sich die Hände. Ein stilles Bild der Versöhnung zwischen zwei Völkern, die sich hier "
     "einst gegenseitig ausbluten ließen. Verdun, neunzehnhundertsechzehn. Im Gedenken an alle Gefallenen beider "
     "Seiten."),
]
