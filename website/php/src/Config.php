<?php

declare(strict_types=1);

namespace Koenigshof\Kontakt;

/**
 * Lädt die Server-Konfiguration (kontakt-config.php) und die gemeinsame
 * Formular-Definition (form-config.json) und prüft sie auf Plausibilität.
 *
 * Die Server-Konfiguration enthält Geheimnisse (SMTP-Passwort, Schlüssel)
 * und liegt deshalb NICHT im Repository und möglichst AUSSERHALB des
 * öffentlich erreichbaren Webverzeichnisses.
 */
final class Config
{
    private const DEFAULTS = [
        'recipient' => '',
        'recipient_name' => '',
        'from' => '',
        'from_name' => 'Website-Kontaktformular',
        'transport' => 'smtp', // smtp | mail | file
        'smtp' => [
            'host' => '',
            'port' => 587,
            'encryption' => 'tls', // tls (STARTTLS) | ssl (SMTPS) | none
            'username' => '',
            'password' => '',
            'timeout' => 15,
        ],
        'secret' => '',
        'allowed_origins' => [],
        'storage_dir' => '',
        'file_transport_dir' => '',
        'rate_limit' => [
            'max_requests' => 5,
            'window_seconds' => 3600,
        ],
        'require_token' => false,
        'site_name' => 'Website',
    ];

    /** @param array<string, mixed> $server @param array<string, mixed> $form */
    private function __construct(private readonly array $server, private readonly array $form)
    {
    }

    /**
     * @param array<string, mixed> $server Inhalt von kontakt-config.php
     * @param array<string, mixed> $form   Inhalt von form-config.json
     */
    public static function fromArrays(array $server, array $form): self
    {
        $merged = array_replace_recursive(self::DEFAULTS, $server);
        $config = new self($merged, $form);
        $config->assertValid();
        return $config;
    }

    /** Sucht die Konfigurationsdatei an den dokumentierten Orten. */
    public static function load(string $formConfigPath, string ...$candidates): self
    {
        $serverConfig = null;
        foreach ($candidates as $path) {
            if ($path !== '' && is_file($path) && is_readable($path)) {
                /** @psalm-suppress UnresolvableInclude */
                $serverConfig = require $path;
                break;
            }
        }
        if (!is_array($serverConfig)) {
            throw new ConfigException('Keine kontakt-config.php gefunden (siehe kontakt-config.example.php).');
        }

        $json = @file_get_contents($formConfigPath);
        $form = $json === false ? null : json_decode($json, true);
        if (!is_array($form)) {
            throw new ConfigException('form-config.json fehlt oder ist ungültig.');
        }

        return self::fromArrays($serverConfig, $form);
    }

    private function assertValid(): void
    {
        $secret = (string) $this->server['secret'];
        if (strlen($secret) < 32 || str_contains($secret, 'BITTE')) {
            throw new ConfigException('"secret" muss ein zufälliger Wert mit mindestens 32 Zeichen sein.');
        }
        if (!in_array($this->transport(), ['smtp', 'mail', 'file'], true)) {
            throw new ConfigException('"transport" muss smtp, mail oder file sein.');
        }
        if ($this->transport() !== 'file') {
            if (!filter_var($this->recipient(), FILTER_VALIDATE_EMAIL) || !filter_var($this->from(), FILTER_VALIDATE_EMAIL)) {
                throw new ConfigException('"recipient" und "from" müssen gültige E-Mail-Adressen sein.');
            }
        }
        if ($this->transport() === 'smtp' && $this->smtp()['host'] === '') {
            throw new ConfigException('Für transport=smtp muss smtp.host gesetzt sein.');
        }
        if ($this->storageDir() === '') {
            throw new ConfigException('"storage_dir" muss gesetzt sein (beschreibbares Verzeichnis, möglichst außerhalb des Webroots).');
        }
        if (!isset($this->form['fields'], $this->form['topics'], $this->form['spam'])) {
            throw new ConfigException('form-config.json ist unvollständig.');
        }
    }

    public function secret(): string
    {
        return (string) $this->server['secret'];
    }

    public function transport(): string
    {
        return (string) $this->server['transport'];
    }

    public function recipient(): string
    {
        return (string) $this->server['recipient'];
    }

    public function recipientName(): string
    {
        return (string) $this->server['recipient_name'];
    }

    public function from(): string
    {
        return (string) $this->server['from'];
    }

    public function fromName(): string
    {
        return (string) $this->server['from_name'];
    }

    public function siteName(): string
    {
        return (string) $this->server['site_name'];
    }

    /** @return array{host: string, port: int, encryption: string, username: string, password: string, timeout: int} */
    public function smtp(): array
    {
        $s = (array) $this->server['smtp'];
        return [
            'host' => (string) $s['host'],
            'port' => (int) $s['port'],
            'encryption' => (string) $s['encryption'],
            'username' => (string) $s['username'],
            'password' => (string) $s['password'],
            'timeout' => (int) $s['timeout'],
        ];
    }

    /** @return list<string> */
    public function allowedOrigins(): array
    {
        return array_values(array_map(
            static fn ($o): string => rtrim(strtolower((string) $o), '/'),
            (array) $this->server['allowed_origins']
        ));
    }

    public function storageDir(): string
    {
        return rtrim((string) $this->server['storage_dir'], '/');
    }

    public function fileTransportDir(): string
    {
        $dir = (string) $this->server['file_transport_dir'];
        return $dir !== '' ? rtrim($dir, '/') : $this->storageDir() . '/mails';
    }

    public function rateLimitMax(): int
    {
        return max(1, (int) $this->server['rate_limit']['max_requests']);
    }

    public function rateLimitWindow(): int
    {
        return max(60, (int) $this->server['rate_limit']['window_seconds']);
    }

    public function requireToken(): bool
    {
        return (bool) $this->server['require_token'];
    }

    /** @return array<string, array<string, mixed>> */
    public function fields(): array
    {
        return (array) $this->form['fields'];
    }

    /** @return list<array{value: string, label: string, subject: string}> */
    public function topics(): array
    {
        return array_values((array) $this->form['topics']);
    }

    /** @return array{honeypotField: string, tokenField: string, minSecondsToSubmit: int, maxTokenAgeSeconds: int, maxLinksInMessage: int} */
    public function spam(): array
    {
        $s = (array) $this->form['spam'];
        return [
            'honeypotField' => (string) $s['honeypotField'],
            'tokenField' => (string) $s['tokenField'],
            'minSecondsToSubmit' => (int) $s['minSecondsToSubmit'],
            'maxTokenAgeSeconds' => (int) $s['maxTokenAgeSeconds'],
            'maxLinksInMessage' => (int) $s['maxLinksInMessage'],
        ];
    }

    public function successPath(): string
    {
        return (string) ($this->form['successPath'] ?? '/kontakt/danke/');
    }

    public function errorPath(): string
    {
        return (string) ($this->form['errorPath'] ?? '/kontakt/fehler/');
    }
}
