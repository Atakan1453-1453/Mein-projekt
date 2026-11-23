<?php

/**
 * Lädt die Klassen des Kontaktformulars im Produktivbetrieb (ohne Composer).
 * Wird beim Build nach dist/api/lib/bootstrap.php kopiert; Verzeichnisstruktur:
 *
 *   api/kontakt.php            ← öffentlicher Endpunkt
 *   api/lib/bootstrap.php      ← diese Datei
 *   api/lib/src/*.php          ← eigene Klassen
 *   api/lib/phpmailer/*.php    ← PHPMailer (LGPL-2.1)
 *   api/lib/form-config.json   ← gemeinsame Formular-Definition
 *   api/lib/.htaccess          ← sperrt den direkten Zugriff
 */

declare(strict_types=1);

if (PHP_VERSION_ID < 80100) {
    http_response_code(500);
    exit('PHP 8.1 oder neuer erforderlich.');
}

date_default_timezone_set('Europe/Berlin');
mb_internal_encoding('UTF-8');

spl_autoload_register(static function (string $class): void {
    $map = [
        'Koenigshof\\Kontakt\\' => __DIR__ . '/src/',
        'PHPMailer\\PHPMailer\\' => __DIR__ . '/phpmailer/',
    ];
    foreach ($map as $prefix => $dir) {
        if (str_starts_with($class, $prefix)) {
            $file = $dir . str_replace('\\', '/', substr($class, strlen($prefix))) . '.php';
            if (is_file($file)) {
                require $file;
            }
            return;
        }
    }
});
