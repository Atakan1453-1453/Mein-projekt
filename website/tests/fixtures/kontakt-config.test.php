<?php

/**
 * Konfiguration NUR für automatisierte Tests: Mails werden als .eml-Dateien
 * nach .tmp/test-storage/mails geschrieben statt versendet.
 */

$storage = dirname(__DIR__, 2) . '/.tmp/test-storage';

return [
    'recipient' => 'center-management@example.test',
    'from' => 'website@example.test',
    'site_name' => 'Galerie Königshof',
    'transport' => 'file',
    'secret' => 'test-secret-only-for-automated-tests-0123456789abcdef',
    'allowed_origins' => ['http://127.0.0.1:4322', 'http://localhost:4322'],
    'storage_dir' => $storage,
    'rate_limit' => ['max_requests' => (int) (getenv('KONTAKT_RATE_LIMIT') ?: 50), 'window_seconds' => 3600],
    'require_token' => false,
];
