# Website Galerie Königshof Mettmann

Statische, schnelle und datenschutzfreundliche Website mit serverseitig geprüftem Kontaktformular.

> **Aktueller Stand: Testversion.** Kontakt-, Impressums- und Datenschutzangaben, Ansprechpartner,
> Services und Galeriebilder sind **fiktive Beispiele** (Mustermann, Musterstadt, example.com).
> Jede Seite zeigt einen Hinweisbalken, Suchmaschinen sind ausgesperrt und `npm run check:launch`
> blockiert den Livegang. Umstellung auf echte Daten: [WARTUNG.md, Abschnitt 3.0](WARTUNG.md#30-von-der-testversion-zum-livebetrieb-).

| | |
|---|---|
| **Technik** | [Astro 7](https://astro.build) (statische Seiten) + PHP 8.1+ (nur für das Kontaktformular) |
| **Hosting** | jedes klassische Webhosting mit PHP und Apache (`.htaccess`) – nginx-Beispiel liegt bei |
| **JavaScript** | insgesamt ca. 7 KB (komprimiert ca. 3,4 KB), nur für Menü, Formular-Komfort und Bildergalerie – alles funktioniert auch ohne |
| **Tracking / Cookies** | keine – daher kein Cookie-Banner nötig |
| **Schriften** | Fraunces & Inter, lokal eingebunden (keine Google-Fonts-Verbindung) |
| **Qualität** | Lighthouse 98–100 in allen Kategorien, WCAG 2.2 AA (axe), 127 Browser- + 43 PHP-Tests |

## Schnellstart

```bash
cd website
npm ci                                   # Node.js ≥ 22.23
composer install --working-dir=php       # PHP ≥ 8.1 + Composer

npm run dev        # Entwicklung mit Live-Reload: http://localhost:4321 (Formular-Versand hier nicht aktiv)
npm run preview    # Produktions-Build + PHP-Server inkl. Formular: http://127.0.0.1:8080
npm test           # alle Prüfungen (Typen, PHP, Build, HTML, Links, Browser-Tests)
npm run check:launch   # Go-Live-Prüfung: schlägt fehl, solange Platzhalter vorhanden sind
```

Für `npm run preview` mit funktionierendem Formular einmalig `php/kontakt-config.example.php` nach
`website/kontakt-config.php` kopieren und `'transport' => 'file'` sowie einen `secret` setzen –
die Test-Mails landen dann als `.eml`-Dateien im `storage_dir`.

## Seiten

| URL | Inhalt |
|---|---|
| `/` | Startseite: Hero, Kennzahlen, Shops, Geschichte, Besuch (Anfahrt/Öffnungszeiten/Parken), Galerie-Vorschau, Vermietungs-CTA |
| `/ueber-uns/` | Geschichte (Zeitleiste), Neustart 2019, Center heute, Center-Management |
| `/shops/` | Shop-Verzeichnis nach Kategorien, Öffnungszeiten & Parken, Services, Vermietung |
| `/galerie/` | Bildergalerie mit barrierefreier Großansicht |
| `/kontakt/` | Kontaktformular (Anliegen-Auswahl, Zusatzfelder für Mietanfragen), Kontaktdaten, Anfahrt |
| `/impressum/`, `/datenschutz/` | Rechtliches (Entwürfe mit fiktiven Musterangaben) |
| `/kontakt/danke/`, `/kontakt/fehler/`, `/404.html` | Status- und Fehlerseiten (noindex) |

## Ordnerstruktur

```
website/
├── src/
│   ├── config/site.ts            ← ALLE Firmendaten, Texte, Shops, Öffnungszeiten
│   ├── config/contact-form.json  ← Formularfelder & Regeln (Browser UND Server)
│   ├── data/gallery.ts           ← Galeriebilder
│   ├── assets/                   ← Bilder (werden automatisch optimiert) & Schriften
│   ├── components/               ← wiederverwendbare Bausteine (Header, Footer, …)
│   ├── layouts/BaseLayout.astro  ← <head>, SEO-Metadaten
│   ├── pages/                    ← eine Datei = eine Seite
│   ├── scripts/                  ← kleines Client-JavaScript (Menü, Formular, Galerie)
│   └── styles/global.css         ← Design-Tokens (Farben, Schriften, Abstände)
├── php/                          ← Formular-Backend (Validierung, Spam-Schutz, SMTP)
│   ├── src/                      ← Klassen
│   ├── tests/                    ← PHPUnit-Tests
│   └── kontakt-config.example.php
├── config/security-headers.json  ← CSP & Sicherheits-Header (→ .htaccess / nginx)
├── deploy/                       ← nginx-Beispielkonfiguration
├── scripts/                      ← Build-, Prüf- und Hilfsskripte
├── tests/e2e/                    ← Playwright-Browser-Tests
├── WARTUNG.md                    ← Anleitung für Pflege und Betrieb
└── GO-LIVE-CHECKLISTE.md         ← was vor der Veröffentlichung zu tun ist
```

Weiterführend: **[WARTUNG.md](WARTUNG.md)** · **[GO-LIVE-CHECKLISTE.md](GO-LIVE-CHECKLISTE.md)**
