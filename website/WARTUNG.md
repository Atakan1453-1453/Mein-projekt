# Wartungsanleitung – Website Galerie Königshof

Diese Anleitung erklärt, wie die Website gepflegt, veröffentlicht und sicher betrieben wird.
Abschnitte mit 🟢 sind auch ohne Programmierkenntnisse machbar; 🟡 erfordert etwas Erfahrung
mit Code-Editor und Kommandozeile.

---

## 1. So funktioniert die Website

```
Browser ──► statische HTML-Seiten (dist/)        ← erzeugt von Astro aus src/
        └─► /api/kontakt.php (PHP)               ← nur für das Kontaktformular
                 ├─ prüft Eingaben & Spam-Schutz
                 └─ sendet E-Mail per SMTP an das Center-Management
```

- **Astro** erzeugt beim „Bauen“ (`npm run build`) fertige HTML-Seiten. Auf dem Server läuft
  dadurch fast nichts – das macht die Seite schnell, sicher und günstig zu hosten.
- **PHP** wird nur für das Kontaktformular gebraucht. Die Formularregeln (Pflichtfelder,
  Längen …) stehen in **einer** Datei (`src/config/contact-form.json`) und gelten für Browser
  und Server gleichermaßen.
- **Keine Datenbank, kein CMS, keine Cookies, kein Tracking.**

---

## 2. Einrichtung des Arbeitsplatzes 🟡

Benötigt: [Node.js](https://nodejs.org) ≥ 22.23, PHP ≥ 8.1 (empfohlen 8.3) mit Erweiterung
`mbstring`, [Composer](https://getcomposer.org).

```bash
cd website
npm ci                                   # JavaScript-Abhängigkeiten (exakt laut package-lock.json)
composer install --working-dir=php       # PHP-Abhängigkeiten (PHPMailer, PHPUnit)
npx playwright install chromium          # Browser für die automatisierten Tests (einmalig)
```

| Befehl | Zweck |
|---|---|
| `npm run dev` | Entwicklungsserver mit Live-Vorschau unter http://localhost:4321 (Formular sendet hier nicht) |
| `npm run build` | Produktionsversion nach `dist/` erzeugen (inkl. PHP-Handler und `.htaccess`) |
| `npm run preview` | Build + lokaler PHP-Server mit funktionierendem Formular: http://127.0.0.1:8080 |
| `npm test` | **alle** automatischen Prüfungen (siehe Abschnitt 6) |
| `npm run check:launch` | Go-Live-Prüfung: listet alle offenen Platzhalter |
| `npm run generate:assets` | Social-Media-Bild, Icons und Galerie-Platzhalter neu erzeugen |

Lokale Formular-Konfiguration für `npm run preview`: `php/kontakt-config.example.php` nach
`website/kontakt-config.php` kopieren, `'transport' => 'file'` und einen `secret` eintragen,
bei `allowed_origins` `http://127.0.0.1:8080` ergänzen. Diese Datei ist per `.gitignore` vom
Repository ausgeschlossen.

---

## 3. Häufige Änderungen

### 3.1 Texte, Kontaktdaten, Öffnungszeiten, Shops 🟢
Fast alle Angaben stehen in **`src/config/site.ts`**:

| Was | Wo in `site.ts` |
|---|---|
| Telefon / E-Mail des Centers | `contact.phone`, `contact.email` |
| Öffnungszeiten | `openingHours` (Anzeige **und** `schema` für Google anpassen!) |
| Kennzahlen (Shops, Parkplätze, Fläche) | `stats` |
| Shop-Liste | `shops` (Name + Kategorie) und `shopsAsOf` (Stand) |
| Parkhaus-Infos, Parkgebühren | `parking` |
| Geschichte | `history` |
| Impressum-Angaben | `operator` |
| Datenschutz-Angaben (Hoster, Mail-Anbieter …) | `privacy` – bei Änderungen `lastUpdated` anpassen |

Ein Wert `null` erscheint auf der Website als gestrichelter **[Platzhalter: …]**. Einfach den
echten Wert in Anführungszeichen eintragen, z. B. `phone: '+49 2104 123456',`.

Seitenspezifische Texte (Überschriften, Absätze) stehen direkt in `src/pages/*.astro` und
lassen sich dort wie normaler Text ändern – nur die Zeichen `{ } < >` nicht anfassen.

**Regel:** Keine Angaben erfinden oder schätzen. Bewertungen, Kundenstimmen, Auszeichnungen
und Zahlen nur mit Beleg und Freigabe veröffentlichen.

### 3.2 Galerie-Fotos austauschen 🟢/🟡
1. Fotos (JPG, mind. 1600 px breit, Querformat 4:3 ideal) nach `src/assets/gallery/` legen,
   z. B. `eingang.jpg`. Dateinamen ohne Umlaute/Leerzeichen.
2. In `src/data/gallery.ts` oben importieren und den Eintrag ersetzen:
   ```ts
   import eingang from '../assets/gallery/eingang.jpg';
   // …
   { src: eingang, caption: 'Haupteingang', alt: 'Glasfront des Haupteingangs an der Talstraße bei Tag' },
   ```
   `placeholder: true` dabei **entfernen**.
3. Nicht mehr verwendete `platzhalter-*.jpg` löschen.
4. Bildnachweis im Impressum ergänzen (`src/pages/impressum.astro`, „Bildnachweise“).

Astro erzeugt automatisch AVIF/WebP in mehreren Größen – Bilder **nicht** vorher verkleinern.
Achten Sie auf **Nutzungsrechte** und darauf, dass erkennbare Personen **eingewilligt** haben.
Der `alt`-Text beschreibt, was zu sehen ist (für blinde Nutzer:innen und Suchmaschinen).

### 3.3 Logo austauschen 🟡
Die aktuelle Wortmarke mit Krone ist ein **Entwurf** (`src/components/Logo.astro`). Für ein
offizielles Logo die SVG-Datei in `Logo.astro` einsetzen, `public/favicon.svg` ersetzen und
`npm run generate:assets` ausführen (erzeugt Social-Media-Bild und App-Icons neu – dort
ggf. die Vorlage in `scripts/generate-assets.mjs` anpassen).

### 3.4 Farben und Schriften 🟡
Alle Farben, Schriftgrößen und Abstände sind zentral als „Design-Tokens“ oben in
`src/styles/global.css` definiert (`--c-royal-800`, `--c-gold-500` …). Neue Farben bitte auf
Kontrast prüfen (Text mind. 4,5 : 1) – `npm test` prüft das automatisch mit axe.
Schriften liegen als `.woff2` in `src/assets/fonts/` (Lizenz: SIL OFL, Lizenztexte daneben).

### 3.5 Kontaktformular anpassen 🟡
- **Anliegen-Auswahl / Feldregeln:** `src/config/contact-form.json` (gilt für Browser und Server).
- **Neues Feld:** zusätzlich in `src/components/ContactForm.astro` (HTML) und in
  `php/src/Mailer.php` (`LABELS` + `buildBody`) ergänzen, dann Datenschutzerklärung anpassen.
- **Empfänger, Absender, SMTP:** nur in der `kontakt-config.php` auf dem Server.

### 3.6 Neue Seite anlegen 🟡
1. Datei in `src/pages/` anlegen (z. B. `veranstaltungen.astro`), eine bestehende Seite als
   Vorlage kopieren. Jede Seite braucht einen eigenen `title` und eine `description`
   (120–160 Zeichen).
2. Falls sie ins Menü soll: in `navigation` in `src/config/site.ts` eintragen.
3. In `tests/e2e/helpers.ts` (`PAGES`) ergänzen, damit sie mitgetestet wird.
Die Sitemap wird automatisch aktualisiert.

### 3.7 Platzhalter-Hinweise in Impressum/Datenschutz entfernen 🟡
Nach rechtlicher Prüfung die Blöcke `<Placeholder label="Rechtliche Prüfung …">` in
`src/pages/impressum.astro` und `src/pages/datenschutz.astro` löschen, ebenso den Block
„Hinweis nach § 36 VSBG“ durch den abgestimmten Text ersetzen.

---

## 4. Veröffentlichen (Deployment) 🟡

### Erstmalig
1. **Build mit der echten Domain:**
   ```bash
   SITE_URL=https://www.ihre-domain.de npm run build
   npm run check:launch          # muss ohne Fehler durchlaufen
   ```
2. **Inhalt von `dist/`** (inkl. der versteckten `.htaccess`-Dateien!) per SFTP in das
   Webverzeichnis (Document Root) hochladen.
3. **`kontakt-config.php`** aus `php/kontakt-config.example.php` erstellen, ausfüllen und
   **eine Ebene über** dem Webverzeichnis ablegen:
   ```
   /home/kunde/
   ├── kontakt-config.php        ← hier (nicht aus dem Internet erreichbar)
   ├── kontakt-storage/          ← wird automatisch angelegt (Rate-Limit)
   └── public_html/              ← Inhalt von dist/
   ```
   Geht das beim Hoster nicht: nach `public_html/api/lib/kontakt-config.php` (Ordner ist gesperrt).
   Dateirechte: `chmod 600 kontakt-config.php`.
4. **Geheimen Schlüssel** erzeugen: `php -r "echo bin2hex(random_bytes(32)), PHP_EOL;"`
5. **PHP-Version** im Hoster-Panel auf ≥ 8.1 (empfohlen 8.3) stellen.
6. **E-Mail-Zustellung absichern:** Die `from`-Adresse muss zur Domain gehören; SPF, DKIM und
   DMARC beim Domain-/Mail-Anbieter einrichten, sonst landen Anfragen im Spam.
7. Punkte aus **GO-LIVE-CHECKLISTE.md** abarbeiten.

### Aktualisierungen
`npm test` → `SITE_URL=… npm run build` → Inhalt von `dist/` hochladen (alte Dateien in
`_astro/` dürfen gelöscht werden). `kontakt-config.php` bleibt unverändert.

### nginx statt Apache
`.htaccess` wird von nginx ignoriert. Vorlage: `deploy/nginx.conf.example`; die Sicherheits-
Header erzeugt jeder Build in `deploy/nginx-security-headers.conf`.

---

## 5. Sicherheit & Datenschutz im Betrieb

- **Sicherheits-Header / Content-Security-Policy** stehen in `config/security-headers.json`
  und werden bei jedem Build in `.htaccess` übernommen. Die CSP erlaubt **nur eigene Dateien** –
  externe Dienste werden blockiert.
- **Externe Dienste einbinden (Google Maps, YouTube, Instagram, Analyse-Tools …)** erfordert
  immer drei Schritte: CSP erweitern, Datenschutzerklärung ergänzen und – bei Übertragung
  personenbezogener Daten an Dritte – eine **Einwilligung vor dem Laden** einholen
  (z. B. Zwei-Klick-Lösung). Ohne das bitte nichts einbinden.
- **Geheimnisse** (SMTP-Passwort, `secret`) nur in `kontakt-config.php` auf dem Server – nie ins
  Repository, nie per E-Mail verschicken.
- **Rate-Limit hinter Proxy/CDN:** Läuft die Seite hinter Cloudflare o. Ä., sehen alle Besucher
  für PHP gleich aus. Dann im Hoster/CDN die echte Besucher-IP an `REMOTE_ADDR` durchreichen
  lassen (z. B. `mod_remoteip`) – sonst greift das Limit für alle gemeinsam.
- **Spam nimmt zu?** In `kontakt-config.php` `'require_token' => true` setzen (Formular dann nur
  mit JavaScript) und/oder `rate_limit.max_requests` senken.
- **Fehlerprotokoll:** Probleme des Formulars landen mit dem Präfix `[kontakt]` im PHP-Error-Log
  des Hosters – ohne personenbezogene Daten.

---

## 6. Automatische Tests 🟡

`npm test` führt nacheinander aus:

| Schritt | Prüft |
|---|---|
| `astro check` | TypeScript-/Template-Fehler |
| `test:php` | 43 PHPUnit-Tests: Validierung, Header-Injection, Token, Rate-Limit, Mail-Aufbau |
| `build` | Build inkl. Selbstprüfung auf CSP-widrigen Inline-Code |
| `validate:html` | HTML-Validität aller Seiten |
| `check:links` | alle internen Links, Bilder und Sprungmarken (`-- --external` prüft auch externe Links) |
| `test:e2e` | 126 Browser-Tests in 4 Bildschirmbreiten: Ladefehler, CSP-Verstöße, horizontales Scrollen, Barrierefreiheit (axe, WCAG 2.2 AA), Tastaturbedienung, Menü, Galerie, Formular inkl. Spam-Schutz und Betrieb ohne JavaScript, SEO-Metadaten, Sicherheits-Header, keine Cookies/Drittanbieter |

Die GitHub-Action `.github/workflows/website.yml` führt dieselben Prüfungen bei jedem Push aus.

**Ladezeit messen** (optional): `npm run preview`, dann
`npx lighthouse@13 http://127.0.0.1:8080/ --view`. Stand bei Übergabe: 98–100 Punkte in allen
Kategorien (mobil und Desktop).

---

## 7. Wartungsplan

| Wann | Aufgabe |
|---|---|
| **monatlich** | Testanfrage über das Formular senden (kommt sie an, nicht im Spam?) · Öffnungszeiten und Shop-Liste prüfen |
| **vierteljährlich** | Abhängigkeiten aktualisieren: `npm outdated`, `npm update`, `composer update --working-dir=php`, danach `npm test` · `npm audit` / `composer audit --working-dir=php` |
| **jährlich** | PHP-Version beim Hoster prüfen (nur unterstützte Versionen nutzen) · Datenschutzerklärung und Impressum auf Aktualität prüfen · Major-Update von Astro prüfen (Changelog lesen) · SSL-Zertifikat (meist automatisch) |
| **bei jeder Änderung** | `npm test` muss grün sein, bevor hochgeladen wird |

Tipp: Dependabot/Renovate im GitHub-Repository aktivieren – dann kommen Update-Vorschläge
automatisch als Pull Request, inklusive Testlauf.

---

## 8. Fehlerbehebung

| Problem | Ursache / Lösung |
|---|---|
| Formular meldet „derzeit nicht verfügbar“ | `kontakt-config.php` fehlt, ist am falschen Ort oder ungültig (z. B. `secret` zu kurz). PHP-Error-Log prüfen (`[kontakt] Konfigurationsfehler: …`). |
| Formular meldet „konnte nicht gesendet werden“ | SMTP-Zugangsdaten/Port falsch oder Server blockiert ausgehende Verbindungen. Error-Log prüfen; ggf. Port 465 mit `'encryption' => 'ssl'` testen. |
| Anfragen landen im Spam | SPF/DKIM/DMARC für die Absender-Domain einrichten; `from` muss eine Adresse der eigenen Domain sein. |
| „500 Internal Server Error“ nach Upload | Hoster erlaubt eine `.htaccess`-Anweisung nicht – meist `Options`. Zeile `Options -Indexes -MultiViews` testweise auskommentieren. |
| Seite ohne Design / Schriften fehlen | Ordner `_astro/` nicht vollständig hochgeladen. |
| Änderungen nicht sichtbar | Neu bauen (`npm run build`) und hochladen; Browser-Cache leeren. |
| `npm test` schlägt bei axe fehl | Meist zu geringer Farbkontrast oder fehlende Beschriftung nach einer Änderung – die Meldung nennt Element und Regel. |
