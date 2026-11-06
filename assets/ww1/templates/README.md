# WarAZ-Vorlagen (Vorschau)

Die Vorlagen sind Code. Diese Bilder zeigen nur, wie sie aussehen.

| Datei | Vorlage | Code |
|---|---|---|
| `intro_title.jpg` | Intro-Titel (Thema groß, Jahr in Rot, Unterzeile, WarAZ-Logo) | `warazlib.cards.title()` |
| `overlays.jpg` | Zähler „Datum · TAG X“, Ortslabel, Datumstitel, Zahl-Karte, Namens-Einblender, KI-Tag | `warazlib.ui.Overlay`, `cards.lower_third`, `cards.ai_tag` |
| `chapter.jpg` | Kapitelkarte | `Overlay.chapter()` |
| `quote.jpg` | Zitat mit Quelle und Datum | `Overlay.quote()` |
| `question.jpg` | Leitfrage (Hook) | `cards.question()` |
| `teaser.jpg` | Teaser „Nächstes Video“ | `cards.teaser()` |
| `endcard.jpg` | Endcard: Abo + 2 Felder für den YouTube-Endbildschirm | `cards.endcard()` |
| `short_layout.jpg`, `short_layout_clip.jpg` | Shorts 9:16: Titel-Plakette, große Untertitel, Fortschrittsbalken | `projects/verdun_1916/shorts.py` |
| `thumbnail_layout.jpg` | Thumbnail 1280×720 | `projects/verdun_1916/thumbnail.py` |

Neu erzeugen: `python3 -m warazlib.template_previews <hintergrund.jpg>`
