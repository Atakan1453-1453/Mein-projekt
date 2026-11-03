"""Sprechertext (Deutsch) – ein Eintrag pro Sprachaufnahme.

`text`   : was der Sprecher liest (Ortsnamen teils lautschriftlich, Zahlen ausgeschrieben,
           damit die KI-Stimme sie sicher richtig ausspricht)
Die Zahlen auf dem Bildschirm stehen in scenes.py.
"""

SEGMENTS = [
    ("intro",
     "Tschanakkale, im Nordwesten der heutigen Türkei. Hier trennt eine schmale Meerenge Europa von Asien: "
     "die Dardanellen. Rund sechzig Kilometer lang, an ihrer engsten Stelle kaum mehr als einen Kilometer breit. "
     "Im Jahr neunzehnhundertfünfzehn blickt die ganze Welt auf dieses Wasser. Acht Monate lang tobt hier eine "
     "der blutigsten Schlachten des Ersten Weltkriegs, zu Wasser und zu Land. Am Ende stehen mehr als "
     "hunderttausend Tote und ein Sieg, der die Geschichte der Türkei für immer prägen wird."),

    ("europa",
     "Sommer neunzehnhundertvierzehn. In Europa beginnt der Erste Weltkrieg. Auf der einen Seite stehen die "
     "Mittelmächte: das Deutsche Kaiserreich und Österreich-Ungarn. Auf der anderen die Entente: Großbritannien, "
     "Frankreich und das Russische Zarenreich. Das Osmanische Reich, geschwächt von den Balkankriegen, schließt "
     "im August ein geheimes Bündnis mit Deutschland. Ende Oktober beschießen osmanische Kriegsschiffe unter "
     "deutschem Kommando russische Häfen am Schwarzen Meer. Anfang November ist das Osmanische Reich im Krieg."),

    ("strategie",
     "Damit sitzt Russland in der Falle. Die Ostsee ist blockiert, und der wichtigste Seeweg zu seinen "
     "Verbündeten führt durch den Bosporus und die Dardanellen. Doch die Osmanen haben die Meerenge gesperrt. "
     "In London entsteht ein kühner Plan, vorangetrieben vom Ersten Lord der Admiralität, Winston Churchill: "
     "Eine Flotte soll die Dardanellen durchbrechen, Istanbul bedrohen und das Osmanische Reich aus dem Krieg "
     "zwingen. Dann wäre der Weg nach Russland frei."),

    ("festung",
     "Doch die Dardanellen sind eine natürliche Festung. An beiden Ufern liegen Forts und Küstenbatterien: "
     "Seddülbahir und Kumkale an der Einfahrt, weiter innen Rumeli Medschidiye, Hamidiye, Kilitbahir und "
     "Tschimenlik, an der engsten Stelle bei Tschanakkale. Dazwischen liegen zehn Reihen von Seeminen, "
     "geschützt von beweglichen Haubitzen und Suchscheinwerfern. Jedes Schiff, das die Minen räumen will, "
     "gerät unter Feuer."),

    ("erster_angriff",
     "Schon am dritten November neunzehnhundertvierzehn beschießen britische und französische Schiffe die "
     "äußeren Forts. Ein Treffer lässt das Pulvermagazin von Seddülbahir explodieren. Der eigentliche Angriff "
     "beginnt am neunzehnten Februar neunzehnhundertfünfzehn. Wochenlang hämmern die Schlachtschiffe auf die "
     "Festungen ein. Doch die Minenfelder im Inneren der Meerenge bleiben unberührt. Die umgebauten "
     "Fischdampfer, die sie räumen sollen, kommen gegen Strömung und Geschützfeuer kaum voran."),

    ("nusret",
     "In der Nacht vom siebten auf den achten März läuft ein kleines Schiff aus: der Minenleger Nusret. "
     "Unbemerkt legt er in der Bucht von Erenköy sechsundzwanzig Minen. Nicht quer zur Fahrrinne wie die "
     "anderen, sondern parallel zum Ufer, genau dort, wo die alliierten Schlachtschiffe bei ihren Angriffen "
     "wenden. Niemand auf der Gegenseite entdeckt die neue Minenreihe."),

    ("maerz_a",
     "Am Morgen des achtzehnten März neunzehnhundertfünfzehn laufen achtzehn Schlachtschiffe in die "
     "Dardanellen ein, vierzehn britische und vier französische, begleitet von Kreuzern und Zerstörern. "
     "In Linien rücken sie vor und nehmen die Forts an der engsten Stelle unter Feuer. Die osmanischen "
     "Geschütze antworten. Stundenlang liegt die Meerenge unter Rauch und Donner."),

    ("maerz_b",
     "Kurz vor zwei Uhr nachmittags läuft das französische Schlachtschiff Bouvet in der Bucht von Erenköy "
     "auf eine Mine. In zwei Minuten kentert es und sinkt. Über sechshundert Seeleute sterben. Am Nachmittag "
     "treffen die Minen der Nusret auch die Briten: Die Inflexible wird schwer beschädigt, die Irresistible "
     "und die Ocean laufen auf Minen und sinken in der Nacht. Die französischen Schiffe Suffren und Gaulois "
     "sind von Granaten schwer getroffen. Drei Schlachtschiffe sind verloren, drei weitere kampfunfähig."),

    ("maerz_c",
     "In der Festung Rumeli Medschidiye, so erzählt die Überlieferung, schleppt Korporal Seyit eine Granate "
     "von über zweihundert Kilo eigenhändig zum Geschütz, nachdem der Ladekran zerstört ist. Am Abend bricht "
     "Admiral de Robeck den Angriff ab. Die Verteidiger haben nur wenige Dutzend Männer verloren. Für die "
     "Osmanen ist der achtzehnte März ein gewaltiger Sieg, der bis heute gefeiert wird. Doch die Alliierten "
     "geben nicht auf. Wenn die Flotte nicht durchkommt, soll das Heer den Weg freikämpfen."),

    ("aufmarsch",
     "General Sir Ian Hamilton erhält den Auftrag. Auf der Insel Limnos, in der Bucht von Moudros, sammelt "
     "sich seine Armee: britische Truppen, das australische und neuseeländische Armeekorps, kurz Anzac, und "
     "ein französisches Korps. Rund fünfundsiebzigtausend Mann. Doch die Vorbereitung dauert fünf Wochen, "
     "und die Osmanen nutzen jeden Tag. Die neue fünfte Armee unter dem deutschen General Otto Liman von "
     "Sanders verteilt rund sechzigtausend Soldaten auf die Halbinsel und das asiatische Ufer."),

    ("verteidigung",
     "Liman von Sanders weiß nicht, wo der Feind landen wird. Zwei Divisionen stehen bei Bolayir, am "
     "schmalen Hals der Halbinsel. Die neunte Division sichert den Süden, zwei weitere das asiatische Ufer "
     "bei Kumkale. In Reserve, bei Edscheabat, liegt die neunzehnte Division. Ihr Kommandeur ist ein junger "
     "Oberstleutnant namens Mustafa Kemal."),

    ("helles",
     "Im Morgengrauen des fünfundzwanzigsten April beginnt die Landung. An der Südspitze der Halbinsel, bei "
     "Kap Helles, geht die britische neunundzwanzigste Division an fünf Stränden an Land. An den Stränden V "
     "und W bei Seddülbahir warten nur wenige hundert osmanische Soldaten, doch ihr Feuer ist verheerend. "
     "Bei V wird der Frachter River Clyde auf Grund gesetzt. Aus seinen Luken stürmen die Soldaten direkt ins "
     "Maschinengewehrfeuer. Das Wasser färbt sich rot. Erst am Abend halten die Briten einen schmalen Streifen "
     "Land."),

    ("anzac",
     "Weiter nördlich landet das Anzac-Korps. Im Dunkeln treiben die Boote rund eineinhalb Kilometer zu weit "
     "nach Norden, in eine kleine Bucht bei Ariburnu, unter steile, zerklüftete Hänge. Die Australier und "
     "Neuseeländer klettern die Grate hinauf, Richtung Dschonkbayiri, dem Höhenzug, der die ganze Halbinsel "
     "beherrscht. Dort trifft Mustafa Kemal mit seinem siebenundfünfzigsten Regiment ein."),

    ("kemal",
     "Er stößt auf Soldaten, die sich ohne Munition zurückziehen, und lässt sie die Bajonette aufpflanzen. "
     "Dann gibt er den Befehl, der berühmt werden wird: Ich befehle euch nicht anzugreifen. Ich befehle euch "
     "zu sterben. In der Zeit, bis wir sterben, können andere Truppen und Kommandeure an unsere Stelle treten. "
     "Die Höhen werden gehalten. Bei Einbruch der Nacht klammern sich rund sechzehntausend Anzac-Soldaten an "
     "einen schmalen Küstenstreifen."),

    ("kumkale",
     "Gleichzeitig landen französische Truppen am asiatischen Ufer bei Kumkale, um die osmanische Artillerie "
     "abzulenken. Nach zwei Tagen harter Kämpfe ziehen sie sich zurück. Bei Bolayir täuscht die britische "
     "Marine eine Landung nur vor, und Liman von Sanders lässt seine Divisionen dort zunächst stehen."),

    ("kirte",
     "Im Süden ist das Ziel der Briten das Dorf Kirte, das sie Krithia nennen, und der Hügel Altschitepe "
     "dahinter. Am achtundzwanzigsten April greifen rund vierzehntausend britische und französische Soldaten an "
     "und kommen kaum voran. Am sechsten Mai folgt der zweite Versuch mit fünfundzwanzigtausend Mann, verstärkt "
     "durch Australier und Neuseeländer. Nach drei Tagen sind sechstausendfünfhundert Angreifer gefallen oder "
     "verwundet. Gewonnen sind nur wenige hundert Meter."),

    ("kirte3",
     "Am vierten Juni wird erneut angegriffen. Dreißigtausend Briten und Franzosen stürmen die osmanischen "
     "Linien. Für einen Moment brechen sie durch, dann werfen Gegenangriffe sie zurück. Ende Juni folgen die "
     "Kämpfe in der Schlucht, die die Briten Gully Ravine nennen. Die osmanischen Gegenangriffe dort kosten "
     "mehr als vierzehntausend Mann. Der Süden der Halbinsel erstarrt im Grabenkrieg, wie an der Westfront."),

    ("mai19",
     "Bei Ariburnu wollen die Osmanen die Eindringlinge ins Meer zurückwerfen. In der Nacht zum neunzehnten "
     "Mai greifen rund zweiundvierzigtausend Soldaten die Stellungen der Anzac an. Doch die Australier und "
     "Neuseeländer sind gewarnt und haben sich tief eingegraben. Bis zum Mittag verlieren die Angreifer rund "
     "zehntausend Mann, dreitausend davon tot. Die Anzac zählen weniger als siebenhundert Verluste."),

    ("waffenruhe",
     "Vor den Gräben liegen Tausende Tote in der Maisonne. Am vierundzwanzigsten Mai vereinbaren beide Seiten "
     "eine Waffenruhe von neun Stunden, um ihre Gefallenen zu begraben. Soldaten, die sich eben noch bekämpft "
     "haben, tauschen Zigaretten. Dann beginnt das Töten von neuem. Die Gräben liegen hier oft nur wenige "
     "Meter auseinander."),

    ("see",
     "Auch auf See wird weitergekämpft. Am dreizehnten Mai versenkt der osmanische Zerstörer Muavenet-i "
     "Milliye nachts das britische Schlachtschiff Goliath. Ende Mai torpediert das deutsche U-Boot U einundzwanzig "
     "die Triumph und die Majestic. Die großen Schiffe ziehen sich zurück. Britische und australische U-Boote "
     "wiederum tauchen unter den Minenfeldern hindurch bis ins Marmarameer."),

    ("sommer",
     "Der Sommer bringt Hitze, Fliegen und Seuchen. Wasser ist knapp, die Ruhr breitet sich aus, Tausende "
     "Männer werden krank. Beide Seiten bringen Verstärkung heran. Hamilton plant einen neuen, großen Schlag: "
     "Er will die Höhen von Dschonkbayiri erobern und mit einer zweiten Landung in der Bucht von Suvla, bei "
     "Anafarta, die osmanische Front umgehen."),

    ("lonepine",
     "Am Nachmittag des sechsten August beginnt die Offensive mit einem Ablenkungsangriff. Australische "
     "Bataillone stürmen die osmanischen Gräben am Kanlisirt, den sie Lone Pine nennen. Die Gräben sind mit "
     "Balken überdeckt, im Halbdunkel wird Mann gegen Mann gekämpft. Vier Tage dauert die Schlacht. "
     "Zweitausendzweihundertsiebenundsiebzig Australier und schätzungsweise sechstausend Osmanen fallen oder "
     "werden verwundet."),

    ("nek",
     "Am Morgen des siebten August greifen australische Leichte Reiter zu Fuß an, an einem schmalen Grat, den "
     "sie The Nek nennen. Vier Wellen laufen nacheinander in das Maschinengewehrfeuer. Von sechshundert "
     "Männern werden dreihundertzweiundsiebzig getötet oder verwundet, in weniger als einer Stunde."),

    ("conk",
     "Das eigentliche Ziel ist Dschonkbayiri. In der Nacht kämpfen sich neuseeländische, britische und indische "
     "Truppen durch die Schluchten nach oben. Am Morgen des achten August erreicht das neuseeländische "
     "Wellington-Bataillon den Gipfel. Den ganzen Tag hält es aus, unter Feuer von allen Seiten. Von "
     "siebenhundertsechzig Männern stehen am Abend nur noch rund siebzig."),

    ("kemal_conk",
     "Mustafa Kemal übernimmt das Kommando über die Front von Anafarta bis Dschonkbayiri. Im Morgengrauen des "
     "zehnten August führt er selbst den Gegenangriff. Mit aufgepflanzten Bajonetten stürmen die osmanischen "
     "Soldaten den Hang hinauf und werfen die Briten vom Gipfel. Ein Granatsplitter trifft Kemal an der Brust, "
     "doch seine Taschenuhr fängt ihn ab. Dschonkbayiri bleibt in osmanischer Hand."),

    ("suvla",
     "Schon in der Nacht zum siebten August landen zwanzigtausend britische Soldaten in der Bucht von Suvla. "
     "Ihnen gegenüber stehen nur rund fünfzehnhundert osmanische Soldaten unter dem deutschen Major Willmer. "
     "Der Weg ins Landesinnere ist offen, doch die britische Führung zögert. Statt vorzurücken, warten die "
     "Truppen am Strand auf Wasser und Befehle. Fast zwei Tage gehen verloren."),

    ("anafarta",
     "Als die Briten am neunten August endlich vorrücken, sind die osmanischen Verstärkungen da und besetzen die "
     "Höhen rund um die Ebene. In den Kämpfen von Anafartalar wird der britische Vorstoß gestoppt. Am "
     "einundzwanzigsten August folgt ein letzter Angriff, am Jusuftschuk Tepe, den die Briten Scimitar Hill "
     "nennen. Von vierzehntausenddreihundert Angreifern fallen fünftausenddreihundert aus. Das Buschland brennt. "
     "Die Augustoffensive ist gescheitert."),

    ("herbst",
     "Im Herbst neunzehnhundertfünfzehn kippt die Lage endgültig. Im Oktober tritt Bulgarien auf der Seite der "
     "Mittelmächte in den Krieg, bald rollen Züge mit deutscher Munition und schwerer Artillerie bis nach "
     "Istanbul. Hamilton wird abgelöst. Sein Nachfolger, General Charles Monro, empfiehlt den Rückzug. Ende "
     "November fegt ein Schneesturm über die Halbinsel. Gräben laufen voll Wasser, Hunderte Männer erfrieren "
     "oder ertrinken."),

    ("rueckzug",
     "Was im Kampf nicht gelang, gelingt im Rückzug. In den Nächten bis zum zwanzigsten Dezember werden "
     "Ariburnu und Suvla geräumt, heimlich, Boot für Boot. Gewehre mit tropfenden Wasserbehältern feuern noch "
     "Schüsse ab, als die letzten Soldaten längst auf See sind. Am neunten Januar neunzehnhundertsechzehn "
     "verlässt der letzte alliierte Soldat Seddülbahir. Bei der gesamten Räumung kommt kaum jemand ums Leben."),

    ("bilanz",
     "Acht Monate Krieg auf engstem Raum. Rund vierhundertneunzigtausend Soldaten haben die Alliierten nach "
     "Gelibolu geschickt, das Osmanische Reich rund dreihundertfünfzehntausend. Mehr als hunderttausend Männer "
     "kehren nie zurück. Nach Angaben des türkischen Generalstabs fallen rund siebenundfünfzigtausend osmanische "
     "Soldaten, andere Schätzungen gehen von bis zu siebenundachtzigtausend aus. Großbritannien und sein "
     "Empire verlieren rund fünfunddreißigtausend Mann, Frankreich fast zehntausend, Australien "
     "achttausendsiebenhundert, Neuseeland zweitausendsiebenhundert."),

    ("erbe",
     "Für die Alliierten ist Gallipoli eine bittere Niederlage. Winston Churchill verliert sein Amt an der "
     "Spitze der Admiralität. In Australien und Neuseeland wird der fünfundzwanzigste April zum Anzac Day, "
     "einem Tag des Gedenkens. Für die Türkei aber ist Tschanakkale weit mehr als ein Sieg. Der Offizier von "
     "Ariburnu und Dschonkbayiri, Mustafa Kemal, wird zum Nationalhelden. Acht Jahre später gründet er die "
     "Republik Türkei, als der spätere Atatürk."),

    ("gedenken",
     "Heute erinnern Friedhöfe und Denkmäler auf der ganzen Halbinsel an die Gefallenen beider Seiten. Bei "
     "Ariburnu steht ein Gedenkstein mit Worten, die Atatürk zugeschrieben werden: Ihr Helden, die ihr euer "
     "Blut vergossen und euer Leben gelassen habt, ihr ruht nun in der Erde eines befreundeten Landes. Für uns "
     "gibt es keinen Unterschied zwischen den Johnnies und den Mehmets, die hier Seite an Seite liegen."),
]

if __name__ == "__main__":
    total = sum(len(t) for _, t in SEGMENTS)
    for k, t in SEGMENTS:
        print(f"{k:16s} {len(t):5d}  ~{len(t)/13.2:5.1f}s")
    print("Summe", total, "Zeichen ~", round(total / 13.2 / 60, 1), "min")
