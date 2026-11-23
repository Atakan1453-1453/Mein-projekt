<?php

/**
 * VORLAGE für die Server-Konfiguration des Kontaktformulars.
 *
 * 1. Diese Datei kopieren und als „kontakt-config.php“ speichern.
 * 2. Am besten EINE EBENE ÜBER dem Webroot ablegen (also neben dem Ordner,
 *    in den der Inhalt von dist/ hochgeladen wird). Dort ist sie aus dem
 *    Internet nicht erreichbar.
 *    Falls der Hoster das nicht erlaubt: nach api/lib/kontakt-config.php
 *    legen (der Ordner ist per .htaccess gesperrt).
 * 3. Werte unten ausfüllen. Diese Datei NIEMALS ins Git-Repository einchecken.
 */

return [
    // Wer die Anfragen erhält
    'recipient' => 'center-management@example.de',
    'recipient_name' => 'Center-Management Galerie Königshof',

    // Absender der Benachrichtigung – muss zur eigenen Domain gehören
    // (sonst landen die Mails wegen SPF/DKIM/DMARC im Spam).
    'from' => 'website@example.de',
    'from_name' => 'Website Galerie Königshof',

    // Kurzname im Betreff, z. B. „[Galerie Königshof] Mietanfrage: Max Muster“
    'site_name' => 'Galerie Königshof',

    // smtp  = Versand über SMTP-Postfach (empfohlen)
    // mail  = PHP mail() des Hosters (nur wenn SMTP nicht möglich)
    // file  = NUR ENTWICKLUNG: speichert Mails als .eml-Dateien
    'transport' => 'smtp',
    'smtp' => [
        'host' => 'smtp.example.de',
        'port' => 587,
        'encryption' => 'tls', // tls = STARTTLS (Port 587), ssl = SMTPS (Port 465)
        'username' => 'website@example.de',
        'password' => 'BITTE-SMTP-PASSWORT-EINTRAGEN',
        'timeout' => 15,
    ],

    // Geheimer Schlüssel für Spam-Schutz-Token und IP-Hashing.
    // Erzeugen mit:  php -r "echo bin2hex(random_bytes(32)), PHP_EOL;"
    'secret' => 'BITTE-ZUFAELLIGEN-SCHLUESSEL-MIT-64-ZEICHEN-EINTRAGEN-0000000000',

    // Erlaubte Herkunft der Formular-Absendungen (exakt, ohne Slash am Ende)
    'allowed_origins' => [
        'https://galeriekoenigshof.de',
        'https://www.galeriekoenigshof.de',
    ],

    // Beschreibbares Verzeichnis für das Rate-Limit (möglichst außerhalb des Webroots)
    'storage_dir' => __DIR__ . '/kontakt-storage',

    // Höchstens X Absendungen pro IP-Adresse innerhalb des Zeitfensters
    'rate_limit' => [
        'max_requests' => 5,
        'window_seconds' => 3600,
    ],

    // true = Formular ohne JavaScript ablehnen (nur aktivieren, falls viel Spam ankommt)
    'require_token' => false,
];
