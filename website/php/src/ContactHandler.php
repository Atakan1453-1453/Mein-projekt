<?php

declare(strict_types=1);

namespace Koenigshof\Kontakt;

/**
 * Ablauf einer Formular-Anfrage:
 *
 *   GET  ?token=1  → neues Spam-Schutz-Token (JSON)
 *   POST           → Größe → Herkunft → Rate-Limit → Honeypot → Token
 *                    → Validierung → Link-Prüfung → Versand
 *
 * Antwortformat: JSON, wenn der Browser es per Accept-Header anfordert
 * (JavaScript-Variante), sonst Weiterleitung auf Danke-/Fehlerseite.
 */
final class ContactHandler
{
    private const MAX_BODY_BYTES = 65536;

    /** @var callable(array<string, string>, \DateTimeImmutable): void */
    private $sender;

    /**
     * @param callable(array<string, string>, \DateTimeImmutable): void $sender Versandfunktion (in Tests austauschbar)
     */
    public function __construct(
        private readonly Config $config,
        private readonly Validator $validator,
        private readonly SpamGuard $spamGuard,
        private readonly RateLimiter $rateLimiter,
        private readonly Token $token,
        callable $sender,
    ) {
        $this->sender = $sender;
    }

    public static function create(Config $config): self
    {
        $token = new Token($config->secret());
        $mailer = new Mailer($config);
        return new self(
            $config,
            new Validator($config),
            new SpamGuard($config, $token),
            new RateLimiter($config->storageDir() . '/ratelimit', $config->secret(), $config->rateLimitMax(), $config->rateLimitWindow()),
            $token,
            static fn (array $data, \DateTimeImmutable $now) => $mailer->send($data, $now),
        );
    }

    /**
     * @param array<string, mixed> $server $_SERVER
     * @param array<string, mixed> $query  $_GET
     * @param array<string, mixed> $post   $_POST
     */
    public function handle(array $server, array $query, array $post, \DateTimeImmutable $now): Response
    {
        $method = strtoupper((string) ($server['REQUEST_METHOD'] ?? 'GET'));
        $wantsJson = str_contains(strtolower((string) ($server['HTTP_ACCEPT'] ?? '')), 'application/json');

        if ($method === 'GET' && isset($query['token'])) {
            return Response::json(200, ['token' => $this->token->issue($now->getTimestamp())]);
        }

        if ($method !== 'POST') {
            return new Response(405, 'Method Not Allowed', ['Allow' => 'POST', 'Content-Type' => 'text/plain; charset=utf-8']);
        }

        if ((int) ($server['CONTENT_LENGTH'] ?? 0) > self::MAX_BODY_BYTES) {
            return $this->fail($wantsJson, 413, ['form' => 'Ihre Nachricht ist zu lang.']);
        }

        if (!$this->isAllowedOrigin($server)) {
            return $this->fail($wantsJson, 403, ['form' => 'Die Anfrage wurde aus Sicherheitsgründen abgelehnt.']);
        }

        $ip = (string) ($server['REMOTE_ADDR'] ?? '0.0.0.0');
        if (!$this->rateLimiter->hit($ip, $now->getTimestamp())) {
            return $this->fail($wantsJson, 429, [
                'form' => 'Sie haben in kurzer Zeit sehr viele Anfragen gesendet. Bitte versuchen Sie es später erneut.',
            ]);
        }

        // Bot hat das unsichtbare Feld ausgefüllt: Erfolg vortäuschen, nichts senden.
        if ($this->spamGuard->isHoneypotFilled($post)) {
            return $this->success($wantsJson);
        }

        $tokenError = $this->spamGuard->tokenError($post, $now->getTimestamp());
        if ($tokenError !== null) {
            return $this->fail($wantsJson, 400, ['form' => $tokenError]);
        }

        ['data' => $data, 'errors' => $errors] = $this->validator->validate($post);
        if ($errors !== []) {
            return $this->fail($wantsJson, 422, $errors);
        }

        if ($this->spamGuard->tooManyLinks($data['nachricht'] ?? '')) {
            $max = $this->config->spam()['maxLinksInMessage'];
            return $this->fail($wantsJson, 422, ['nachricht' => sprintf('Bitte verwenden Sie höchstens %d Links in Ihrer Nachricht.', $max)]);
        }

        try {
            ($this->sender)($data, $now);
        } catch (\Throwable $e) {
            // Keine personenbezogenen Daten ins Log schreiben – nur die technische Ursache.
            error_log('[kontakt] Versand fehlgeschlagen: ' . get_class($e) . ': ' . $e->getMessage());
            return $this->fail($wantsJson, 500, [
                'form' => 'Ihre Nachricht konnte gerade nicht gesendet werden. Bitte versuchen Sie es später erneut oder kontaktieren Sie uns telefonisch.',
            ]);
        }

        return $this->success($wantsJson);
    }

    /**
     * Schutz gegen Formular-Absendungen von fremden Websites:
     * Browser senden bei POST den Origin-Header bzw. Sec-Fetch-Site mit.
     *
     * @param array<string, mixed> $server
     */
    private function isAllowedOrigin(array $server): bool
    {
        $fetchSite = strtolower((string) ($server['HTTP_SEC_FETCH_SITE'] ?? ''));
        if ($fetchSite === 'cross-site') {
            return false;
        }

        $origin = rtrim(strtolower((string) ($server['HTTP_ORIGIN'] ?? '')), '/');
        if ($origin === '' || $origin === 'null') {
            // Kein Origin (ältere Browser, manche Bots): wird über die übrigen Prüfungen abgesichert.
            return $origin === '';
        }

        $allowed = $this->config->allowedOrigins();
        if ($allowed === []) {
            // Nicht konfiguriert: nur gleiche Herkunft wie der aufgerufene Host zulassen.
            $host = strtolower((string) ($server['HTTP_HOST'] ?? ''));
            return $host !== '' && in_array($origin, ['https://' . $host, 'http://' . $host], true);
        }

        return in_array($origin, $allowed, true);
    }

    private function success(bool $wantsJson): Response
    {
        return $wantsJson
            ? Response::json(200, ['ok' => true, 'redirect' => $this->config->successPath()])
            : Response::redirect($this->config->successPath());
    }

    /** @param array<string, string> $errors */
    private function fail(bool $wantsJson, int $status, array $errors): Response
    {
        $headers = $status === 429 ? ['Retry-After' => '600'] : [];
        if ($wantsJson) {
            $response = Response::json($status, ['ok' => false, 'errors' => $errors]);
            return new Response($response->status, $response->body, $response->headers + $headers);
        }
        return Response::redirect($this->config->errorPath());
    }
}
