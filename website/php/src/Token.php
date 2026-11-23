<?php

declare(strict_types=1);

namespace Koenigshof\Kontakt;

/**
 * Signiertes Zeit-Token für den Spam-Schutz.
 *
 * Aufbau:  <ausgestellt-um>.<zufallswert>.<HMAC-SHA256>
 * Das Token beweist, dass das Formular von unserem Server stammt, und
 * erlaubt die Prüfung „zu schnell abgeschickt“ ohne Cookies oder Sessions.
 */
final class Token
{
    public const VALID = 'valid';
    public const INVALID = 'invalid';
    public const TOO_FAST = 'too_fast';
    public const EXPIRED = 'expired';

    public function __construct(private readonly string $secret)
    {
    }

    public function issue(int $now): string
    {
        $payload = $now . '.' . bin2hex(random_bytes(12));
        return $payload . '.' . $this->sign($payload);
    }

    /** @return self::VALID|self::INVALID|self::TOO_FAST|self::EXPIRED */
    public function verify(string $token, int $now, int $minSeconds, int $maxAge): string
    {
        if (strlen($token) > 200 || !preg_match('/^(\d{9,12})\.([a-f0-9]{24})\.([a-f0-9]{64})$/', $token, $m)) {
            return self::INVALID;
        }
        $payload = $m[1] . '.' . $m[2];
        if (!hash_equals($this->sign($payload), $m[3])) {
            return self::INVALID;
        }
        $age = $now - (int) $m[1];
        if ($age < 0) {
            return self::INVALID;
        }
        if ($age < $minSeconds) {
            return self::TOO_FAST;
        }
        if ($age > $maxAge) {
            return self::EXPIRED;
        }
        return self::VALID;
    }

    private function sign(string $payload): string
    {
        return hash_hmac('sha256', 'kontakt-token|' . $payload, $this->secret);
    }
}
