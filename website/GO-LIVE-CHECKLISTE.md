# Go-Live-Checkliste – Website Galerie Königshof

Die Website ist technisch für den Produktivbetrieb vorbereitet. **Vor der Veröffentlichung**
müssen die folgenden Punkte manuell erledigt bzw. geprüft werden. Automatisch prüfbar ist nur
ein Teil: `npm run check:launch` schlägt fehl, solange Platzhalter im Build stehen.

---

## 0. Testversion beenden

Der aktuelle Stand enthält **fiktive Beispielangaben** (Mustermann-Impressum, Ansprechpartner,
Services, Parkgebühren, Kontaktdaten, Symbolbilder). Vorgehen: WARTUNG.md, Abschnitt 3.0.

- [ ] Alle `demo('…')`-Werte und `demoContent` in `src/config/site.ts` durch echte Angaben ersetzt
- [ ] `<Demo …>`-Hüllen in den Seiten entfernt, Galerie ohne `demo: true`
- [ ] `DEMO_MODE = false` (kein Hinweisbalken, kein noindex, robots.txt offen)

## A. Freigabe & Inhalte (Center-Management / Betreiber)

- [ ] **Auftrag/Freigabe klären:** Die Website verwendet Name und Adresse der Galerie Königshof. Vor
      der Veröffentlichung muss der Betreiber den Auftritt freigeben – ebenso Wortmarke/Logo
      (aktuell ein Entwurf; ggf. offizielles Logo einsetzen, Markenrechte beachten).
- [ ] **Alle Fakten bestätigen lassen** (aus öffentlicher Recherche, Stand Okt. 2026 – siehe
      Quellen im Haupt-README):
  - [ ] Shop-Liste (`site.shops`) – vollständiges, aktuelles Verzeichnis eintragen
  - [ ] Kennzahlen: „20+ Shops“, „400+ Parkplätze“, „ca. 15.000 m² Mietfläche“
  - [ ] Öffnungszeiten Mo–Sa 10–19 Uhr (Feiertage/Sonderöffnungen?), Parkhaus 24 h
  - [ ] Parkhaus: schrankenlos, Bezahlung am Automaten/per App; **Parkgebühren** ergänzen
  - [ ] Geschichte: 1972 Kaufhaus / Hertie bis 2009 / Umbau / Wiedereröffnung 7.11.2019,
        14 Monate Umbau, über 10 Mio. € Investition
  - [ ] Domain `galeriekoenigshof.de` (www oder ohne www?)
- [ ] **Kontaktdaten** des Center-Managements (Telefon, E-Mail) → `site.contact`
- [ ] **Center-Management vorstellen** (Seite „Über uns“): Namen/Funktion – Fotos nur mit Einwilligung
- [ ] **Services im Center** (Barrierefreiheit, Aufzüge, WC, Wickelraum …) – nur Bestätigtes
- [ ] **Anliegen im Formular** passen? (Vermietung, Werbung & Aktionen, Presse, Allgemein –
      `src/config/contact-form.json`) und wer erhält die Anfragen?
- [ ] **Echte Fotos** für die Galerie (9 Platzhalter) – mit Nutzungsrechten; Bildnachweise ins Impressum
- [ ] Texte final Korrektur lesen (Tonalität, Rechtschreibung)

## B. Rechtliches

- [ ] **Impressum** vollständig (§ 5 DDG): Betreiber mit Rechtsform, Anschrift,
      Vertretungsberechtigte, Telefon + E-Mail, Registergericht + -nummer, USt-IdNr.,
      Verantwortliche/r nach § 18 Abs. 2 MStV → `site.operator`
- [ ] Entscheidung **Verbraucherstreitbeilegung** (§ 36 VSBG) treffen und Text einsetzen
- [ ] **Datenschutzerklärung** vervollständigen (`site.privacy`): Hoster, E-Mail-Anbieter,
      Datenschutzbeauftragte/r, Log-Speicherdauer; zuständige Aufsichtsbehörde prüfen
- [ ] **Impressum und Datenschutzerklärung rechtlich prüfen lassen** (Anwalt/Datenschutzbeauftragte/r),
      danach die Hinweisblöcke „Rechtliche Prüfung …“ entfernen (WARTUNG.md 3.7)
- [ ] **Auftragsverarbeitungsverträge (Art. 28 DSGVO)** mit Webhoster und E-Mail-Anbieter abschließen
- [ ] Eintrag ins **Verzeichnis der Verarbeitungstätigkeiten** (Kontaktformular, Server-Logs)

## C. Server & Technik

- [ ] Build mit echter Domain: `SITE_URL=https://… npm run build`
- [ ] `npm test` und `npm run check:launch` laufen **fehlerfrei**
- [ ] `dist/` vollständig hochgeladen – inkl. `.htaccess`, `_astro/.htaccess`, `api/lib/.htaccess`
- [ ] **PHP ≥ 8.1** (empfohlen 8.3) aktiv
- [ ] **`kontakt-config.php`** außerhalb des Webroots, `chmod 600`, eigener zufälliger `secret`,
      `allowed_origins` = echte Domain(s), `transport` = `smtp`
- [ ] SMTP-Zugang funktioniert; **SPF, DKIM, DMARC** für die Absender-Domain eingerichtet
- [ ] **SSL-Zertifikat** aktiv; http → https leitet um
- [ ] **Kanonische Domain** festlegen und Weiterleitung www ↔ ohne www in `.htaccess` aktivieren
      (vorbereitet, auskommentiert; ggf. `site`-Domain in `astro.config.mjs` anpassen)
- [ ] Sicherheits-Header live prüfen: `curl -sI https://domain/ | grep -iE "content-security|strict-transport|x-frame"`
      oder securityheaders.com → Ziel: Note A
- [ ] `https://domain/api/lib/form-config.json` liefert **403**; `https://domain/gibtsnicht` liefert die 404-Seite
- [ ] HSTS: läuft alles stabil per HTTPS, kann `max-age` beibehalten und später ggf.
      `includeSubDomains` ergänzt werden (nur wenn **alle** Subdomains HTTPS haben)
- [ ] Hinter CDN/Proxy? → echte Besucher-IP durchreichen (WARTUNG.md, Abschnitt 5)
- [ ] **Bisherige Website:** Gibt es unter der Domain bereits Seiten (z. B. `/oeffnungszeiten-2/`)?
      Dann **301-Weiterleitungen** von alten auf neue URLs einrichten, damit Google-Rankings und
      Lesezeichen erhalten bleiben.

## D. Funktionstest nach dem Livegang

- [ ] Für **jedes Anliegen** eine Testanfrage senden → kommt an, nicht im Spam, „Antworten“ geht an Absender
- [ ] Formular **ohne JavaScript** testen (Browser-Einstellungen) → Danke-Seite
- [ ] Fehlerfall: Pflichtfeld leer lassen → verständliche Meldung
- [ ] **Echte Geräte:** iPhone (Safari), Android (Chrome), Tablet, Desktop
- [ ] **Weitere Browser:** Firefox, Safari, Edge (automatisierte Tests liefen nur in Chromium)
- [ ] Kurztest mit **Screenreader** (VoiceOver bzw. NVDA) und **200 % Zoom**
- [ ] Alle Links klicken, inkl. „Route planen“ (OpenStreetMap)
- [ ] Vorschau beim Teilen (WhatsApp/LinkedIn/Facebook) zeigt Titel + Bild

## E. Sichtbarkeit (SEO) nach dem Livegang

- [ ] **Google Search Console** und **Bing Webmaster Tools**: Domain bestätigen, Sitemap
      `https://domain/sitemap-index.xml` einreichen
- [ ] **Google-Unternehmensprofil** (Maps): Name, Adresse, Öffnungszeiten, Website-Link identisch
      zur Website halten
- [ ] Nach 1–2 Wochen: Indexierung und „Core Web Vitals“ in der Search Console prüfen

---

**Wenn alles abgehakt ist:** `npm run check:launch` zeigt „✓ Keine Platzhalter mehr im Build“ –
die Website kann veröffentlicht werden.
