<?php

/**
 * Öffentlicher Endpunkt des Kontaktformulars: /api/kontakt.php
 *
 * Die Konfiguration (Empfänger, SMTP, geheimer Schlüssel) wird an folgenden
 * Orten gesucht – der erste Treffer gewinnt:
 *   1. Pfad aus der Umgebungsvariable KONTAKT_CONFIG
 *   2. eine Ebene ÜBER dem Webroot:  ../kontakt-config.php   (empfohlen)
 *   3. im gesperrten Bibliotheksordner: api/lib/kontakt-config.php
 *
 * Vorlage: php/kontakt-config.example.php
 */

declare(strict_types=1);

require __DIR__ . '/lib/bootstrap.php';

use Koenigshof\Kontakt\Config;
use Koenigshof\Kontakt\ConfigException;
use Koenigshof\Kontakt\ContactHandler;
use Koenigshof\Kontakt\Response;

// Fehler nie im Browser ausgeben (würde ggf. Pfade/Details verraten).
ini_set('display_errors', '0');

try {
    $config = Config::load(
        __DIR__ . '/lib/form-config.json',
        (string) getenv('KONTAKT_CONFIG'),
        dirname(__DIR__, 2) . '/kontakt-config.php',
        __DIR__ . '/lib/kontakt-config.php',
    );
} catch (ConfigException $e) {
    error_log('[kontakt] Konfigurationsfehler: ' . $e->getMessage());
    $wantsJson = str_contains(strtolower((string) ($_SERVER['HTTP_ACCEPT'] ?? '')), 'application/json');
    ($wantsJson
        ? Response::json(503, ['ok' => false, 'errors' => ['form' => 'Das Kontaktformular ist derzeit nicht verfügbar. Bitte kontaktieren Sie uns telefonisch oder per E-Mail.']])
        : Response::redirect('/kontakt/fehler/'))->send();
    exit;
}

ContactHandler::create($config)
    ->handle($_SERVER, $_GET, $_POST, new DateTimeImmutable('now'))
    ->send();
