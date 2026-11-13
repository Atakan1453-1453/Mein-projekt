# Aylin – KI-Begleiterin im Videoanruf

**Live-Seite:** https://claude.ai/artifact/Tj53STeSkS96k8bEzqry2M

Du rufst Aylin an und siehst sie live im Video. Sie sieht dich nicht (deine Kamera bleibt aus).
Du schreibst ihr, sie liest deine Nachricht, antwortet mit ihrer Stimme und mit Untertiteln, und
im Chat steht alles noch einmal zum Nachlesen.

## So entsteht das Live-Video

Aus Aylins Foto wurden mit Higgsfield (Kling 4.0) fünf Videoclips erstellt. Jeder Clip beginnt
und endet auf demselben Bild, deshalb lassen sich die Clips nahtlos wiederholen und ineinander
überblenden. Die Seite wählt je nach Situation den passenden Clip:

| Clip | Wann | Länge |
|---|---|---|
| `clips/idle` | Sie hört zu: blinzelt, atmet, schaut kurz zur Seite | 10 s, Schleife |
| `clips/read` | Deine Nachricht kommt an, sie liest | 6 s |
| `clips/talk` | Sie spricht | 10 s, Schleife |
| `clips/laugh` | Ihre Antwort enthält *lacht* | 5 s |
| `clips/wave` | Begrüßung oder *winkt* | 5 s |

Jeder Clip liegt als MP4 (H.264) und WebM (VP9) vor. Die Lippenbewegungen sind allgemeine
Sprechbewegungen und nicht Wort für Wort synchron zur Stimme.

## Dateien

| Datei | Inhalt |
|---|---|
| `aylin.html` | Die Videoanruf-Seite (läuft als Claude-Artifact, Antworten über dein Claude-Konto) |
| `clips/` | Die fünf Videoclips (720 × 960, ohne Ton) |
| `poster.jpg`, `aylin-1.jpg` | Standbild und Profilbild |
| `aylin-2.jpg`, `bilder/` | Zweite Bildvariante und die generierten Originale (1536 × 2048) |

## Was die Seite kann

* Anrufen und Auflegen, Gesprächsdauer, Selbstansicht „Kamera aus“
* Stimme (Chrome, Edge, Claude-Desktop-App) mit Untertiteln, die Satz für Satz mitlaufen
* Spracheingabe per Mikrofon: einmal tippen zum Sprechen, nochmal tippen zum Senden
* Einstellungen: dein Name, Stimmfarbe, Antworttempo, eigene Wünsche an Aylin
* Der Verlauf bleibt im Browser gespeichert, Aylin erinnert sich beim nächsten Anruf

Die Persönlichkeit steht in `aylin.html` in der Funktion `persona()`.
