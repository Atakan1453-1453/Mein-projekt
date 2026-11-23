<?php

declare(strict_types=1);

namespace Koenigshof\Kontakt;

/**
 * Einfache, dateibasierte Begrenzung der Anfragen pro IP-Adresse.
 *
 * Datenschutz: Die IP-Adresse wird nie im Klartext gespeichert, sondern nur
 * als HMAC-Hash (mit geheimem Schlüssel). Einträge, die älter als das
 * Zeitfenster sind, werden bei jedem Zugriff automatisch gelöscht.
 */
final class RateLimiter
{
    public function __construct(
        private readonly string $dir,
        private readonly string $secret,
        private readonly int $maxRequests,
        private readonly int $windowSeconds,
    ) {
    }

    /**
     * Registriert einen Versuch und gibt zurück, ob er erlaubt ist.
     */
    public function hit(string $clientIp, int $now): bool
    {
        $this->ensureDir();
        // Aufräumen nach echter Uhrzeit (Dateizeitstempel stammen vom Dateisystem).
        $this->sweep(time());

        $file = $this->dir . '/' . hash_hmac('sha256', 'ratelimit|' . $clientIp, $this->secret) . '.json';
        $handle = @fopen($file, 'c+');
        if ($handle === false) {
            // Speicher nicht verfügbar: lieber durchlassen als legitime Anfragen blockieren.
            error_log('[kontakt] Rate-Limit-Speicher nicht beschreibbar.');
            return true;
        }

        try {
            flock($handle, LOCK_EX);
            $raw = stream_get_contents($handle);
            $hits = is_string($raw) && $raw !== '' ? json_decode($raw, true) : [];
            $hits = is_array($hits) ? $hits : [];
            $threshold = $now - $this->windowSeconds;
            $hits = array_values(array_filter($hits, static fn ($t): bool => is_int($t) && $t > $threshold));

            $allowed = count($hits) < $this->maxRequests;
            if ($allowed) {
                $hits[] = $now;
            }

            ftruncate($handle, 0);
            rewind($handle);
            fwrite($handle, json_encode($hits, JSON_THROW_ON_ERROR));
            fflush($handle);

            return $allowed;
        } finally {
            flock($handle, LOCK_UN);
            fclose($handle);
        }
    }

    /**
     * Löscht alle Einträge, deren letzter Zugriff (Datei-Änderungszeit) länger
     * als das Zeitfenster zurückliegt. $now = aktuelle Unix-Zeit.
     */
    public function sweep(int $now): void
    {
        if (!is_dir($this->dir)) {
            return;
        }
        foreach (glob($this->dir . '/*.json') ?: [] as $file) {
            $mtime = @filemtime($file);
            if ($mtime !== false && $mtime < $now - $this->windowSeconds) {
                @unlink($file);
            }
        }
    }

    private function ensureDir(): void
    {
        if (!is_dir($this->dir)) {
            @mkdir($this->dir, 0700, true);
        }
        // Schutz, falls das Verzeichnis doch im Webroot liegt (Apache).
        $htaccess = $this->dir . '/.htaccess';
        if (is_dir($this->dir) && !is_file($htaccess)) {
            @file_put_contents($htaccess, "Require all denied\n");
        }
    }
}
