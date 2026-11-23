<?php

declare(strict_types=1);

namespace Koenigshof\Kontakt;

/** Einfache HTTP-Antwort (testbar, ohne direkte header()-Aufrufe). */
final class Response
{
    /** @param array<string, string> $headers */
    public function __construct(
        public readonly int $status,
        public readonly string $body = '',
        public readonly array $headers = [],
    ) {
    }

    /** @param array<string, mixed> $payload */
    public static function json(int $status, array $payload): self
    {
        return new self($status, (string) json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), [
            'Content-Type' => 'application/json; charset=utf-8',
        ]);
    }

    public static function redirect(string $location): self
    {
        return new self(303, '', ['Location' => $location]);
    }

    public function send(): void
    {
        http_response_code($this->status);
        header('Cache-Control: no-store, max-age=0');
        header('X-Content-Type-Options: nosniff');
        header('Referrer-Policy: strict-origin-when-cross-origin');
        header_remove('X-Powered-By');
        foreach ($this->headers as $name => $value) {
            header($name . ': ' . $value);
        }
        echo $this->body;
    }
}
