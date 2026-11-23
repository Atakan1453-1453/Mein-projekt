<?php

declare(strict_types=1);

namespace Koenigshof\Kontakt;

/**
 * Spam-Schutz ohne Drittanbieter und ohne Cookies:
 *  1. Honeypot: unsichtbares Feld, das nur Bots ausfüllen.
 *  2. Zeit-Token: Formular darf nicht schneller als in X Sekunden abgeschickt werden.
 *  3. Link-Grenze: Nachrichten mit vielen URLs sind fast immer Spam.
 */
final class SpamGuard
{
    public const OK = 'ok';
    /** Bot erkannt → still „Erfolg“ melden, aber nichts senden. */
    public const SILENT_DROP = 'silent_drop';

    public function __construct(private readonly Config $config, private readonly Token $token)
    {
    }

    /** @param array<string, mixed> $input */
    public function isHoneypotFilled(array $input): bool
    {
        $value = $input[$this->config->spam()['honeypotField']] ?? '';
        return !is_string($value) || trim($value) !== '';
    }

    /**
     * Prüft das Zeit-Token. Gibt eine Fehlermeldung zurück oder null, wenn alles passt.
     * Fehlt das Token (Formular ohne JavaScript), wird es nur bei require_token abgelehnt.
     *
     * @param array<string, mixed> $input
     */
    public function tokenError(array $input, int $now): ?string
    {
        $spam = $this->config->spam();
        $token = $input[$spam['tokenField']] ?? '';
        if (!is_string($token) || $token === '') {
            return $this->config->requireToken()
                ? 'Bitte aktivieren Sie JavaScript oder schreiben Sie uns eine E-Mail.'
                : null;
        }

        return match ($this->token->verify($token, $now, $spam['minSecondsToSubmit'], $spam['maxTokenAgeSeconds'])) {
            Token::VALID => null,
            Token::TOO_FAST => 'Das ging sehr schnell – bitte warten Sie einen Moment und senden Sie das Formular erneut.',
            Token::EXPIRED => 'Das Formular war zu lange geöffnet. Bitte laden Sie die Seite neu und senden Sie es erneut.',
            default => 'Das Formular ist ungültig. Bitte laden Sie die Seite neu und versuchen Sie es erneut.',
        };
    }

    public function tooManyLinks(string $message): bool
    {
        $count = preg_match_all('~(https?://|www\.|\[url)~i', $message);
        return $count > $this->config->spam()['maxLinksInMessage'];
    }
}
