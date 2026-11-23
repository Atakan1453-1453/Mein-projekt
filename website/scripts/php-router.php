<?php

/**
 * Router für den eingebauten PHP-Webserver – NUR für lokale Vorschau und Tests:
 *
 *   php -S 127.0.0.1:8080 -t dist scripts/php-router.php
 *
 * Bildet die wichtigsten Regeln der .htaccess nach (Sicherheits-Header,
 * gesperrte Ordner, Verzeichnis-Index, 404-Seite), damit Tests unter
 * realistischen Bedingungen laufen – insbesondere mit derselben
 * Content-Security-Policy wie im Live-Betrieb.
 */

declare(strict_types=1);

$docroot = rtrim((string) $_SERVER['DOCUMENT_ROOT'], '/');
$path = rawurldecode((string) parse_url((string) $_SERVER['REQUEST_URI'], PHP_URL_PATH));

header_remove('X-Powered-By');

// Sicherheits-Header aus derselben Quelle wie .htaccess
$config = json_decode((string) file_get_contents(__DIR__ . '/../config/security-headers.json'), true);
foreach ($config['headers'] as $name => $value) {
    if ($name === 'Strict-Transport-Security') {
        continue; // lokal kein HTTPS
    }
    if ($name === 'Content-Security-Policy') {
        $value = trim(str_replace('upgrade-insecure-requests', '', $value), '; ');
    }
    header($name . ': ' . $value);
}

$deny = static function (): bool {
    http_response_code(403);
    header('Content-Type: text/plain; charset=utf-8');
    echo 'Forbidden';
    return true;
};

// Gesperrte Bereiche (wie .htaccess)
if (str_contains($path, '..') || preg_match('#(^|/)\.#', $path) || preg_match('#^/api/lib(/|$)#', $path)) {
    return $deny();
}

// PHP-Endpunkt ausführen
if ($path === '/api/kontakt.php') {
    $_SERVER['SCRIPT_FILENAME'] = $docroot . '/api/kontakt.php';
    $_SERVER['SCRIPT_NAME'] = '/api/kontakt.php';
    require $docroot . '/api/kontakt.php';
    return true;
}
if (str_ends_with($path, '.php')) {
    return $deny();
}

$file = $docroot . $path;
if (is_dir($file)) {
    if (!str_ends_with($path, '/')) {
        header('Location: ' . $path . '/', true, 301);
        return true;
    }
    $file .= 'index.html';
}

if (!is_file($file)) {
    http_response_code(404);
    header('Content-Type: text/html; charset=utf-8');
    readfile($docroot . '/404.html');
    return true;
}

$types = [
    'html' => 'text/html; charset=utf-8',
    'css' => 'text/css; charset=utf-8',
    'js' => 'text/javascript; charset=utf-8',
    'json' => 'application/json',
    'xml' => 'application/xml; charset=utf-8',
    'txt' => 'text/plain; charset=utf-8',
    'svg' => 'image/svg+xml',
    'png' => 'image/png',
    'jpg' => 'image/jpeg',
    'jpeg' => 'image/jpeg',
    'webp' => 'image/webp',
    'avif' => 'image/avif',
    'ico' => 'image/x-icon',
    'woff2' => 'font/woff2',
    'webmanifest' => 'application/manifest+json',
];
$ext = strtolower(pathinfo($file, PATHINFO_EXTENSION));
header('Content-Type: ' . ($types[$ext] ?? 'application/octet-stream'));
header('Content-Length: ' . (string) filesize($file));
readfile($file);
return true;
