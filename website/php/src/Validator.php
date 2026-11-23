<?php

declare(strict_types=1);

namespace Koenigshof\Kontakt;

/**
 * Serverseitige Prüfung und Bereinigung der Formulareingaben.
 *
 * Grundsätze:
 *  - Nur bekannte Felder werden übernommen (Whitelist aus form-config.json).
 *  - Alle Werte müssen gültiges UTF-8 sein; Steuerzeichen werden entfernt.
 *  - Einzeilige Felder dürfen keine Zeilenumbrüche enthalten
 *    (verhindert E-Mail-Header-Injection).
 *  - Längen werden in Zeichen (nicht Bytes) gemessen.
 */
final class Validator
{
    /** Felder, die mehrzeilig sein dürfen. */
    private const MULTILINE = ['nachricht'];

    public function __construct(private readonly Config $config)
    {
    }

    /**
     * @param array<string, mixed> $input Rohdaten (z. B. $_POST)
     * @return array{data: array<string, string>, errors: array<string, string>}
     */
    public function validate(array $input): array
    {
        $data = [];
        $errors = [];
        $fields = $this->config->fields();

        // 1. Anliegen zuerst – davon hängen die Zusatzfelder ab.
        $topicValues = array_column($this->config->topics(), 'value');
        $topic = $this->clean($input['anliegen'] ?? '', false);
        if ($topic === null || $topic === '') {
            $errors['anliegen'] = 'Bitte wählen Sie Ihr Anliegen aus.';
        } elseif (!in_array($topic, $topicValues, true)) {
            $errors['anliegen'] = 'Bitte wählen Sie ein gültiges Anliegen aus.';
        } else {
            $data['anliegen'] = $topic;
        }

        foreach ($fields as $name => $rules) {
            if ($name === 'anliegen') {
                continue;
            }
            // Felder, die nur für ein bestimmtes Anliegen gelten, sonst verwerfen.
            if (isset($rules['onlyFor']) && ($data['anliegen'] ?? null) !== $rules['onlyFor']) {
                continue;
            }

            $multiline = in_array($name, self::MULTILINE, true);
            $raw = $input[$name] ?? '';

            if (is_array($raw)) {
                $errors[$name] = 'Ungültige Eingabe.';
                continue;
            }

            $value = $this->clean($raw, $multiline);
            if ($value === null) {
                $errors[$name] = 'Die Eingabe enthält ungültige Zeichen.';
                continue;
            }

            if (!$multiline && preg_match('/[\r\n]/', (string) $raw) === 1) {
                // Zeilenumbruch in einzeiligem Feld: bei Name/E-Mail ablehnen (Header-Injection-Versuch),
                // sonst durch Leerzeichen ersetzen.
                if (in_array($name, ['name', 'email'], true)) {
                    $errors[$name] = 'Die Eingabe enthält ungültige Zeichen.';
                    continue;
                }
            }

            $required = (bool) ($rules['required'] ?? false);
            if ($value === '') {
                if ($required) {
                    $errors[$name] = $this->requiredMessage($name);
                }
                continue;
            }

            $length = mb_strlen($value, 'UTF-8');
            if (isset($rules['minLength']) && $length < (int) $rules['minLength']) {
                $errors[$name] = sprintf('Bitte mindestens %d Zeichen eingeben (aktuell %d).', (int) $rules['minLength'], $length);
                continue;
            }
            if (isset($rules['maxLength']) && $length > (int) $rules['maxLength']) {
                $errors[$name] = sprintf('Bitte höchstens %d Zeichen eingeben.', (int) $rules['maxLength']);
                continue;
            }
            if (isset($rules['pattern']) && preg_match('~' . str_replace('~', '\~', (string) $rules['pattern']) . '~u', $value) !== 1) {
                $errors[$name] = 'Bitte nur Ziffern, Leerzeichen und + ( ) / - verwenden.';
                continue;
            }
            if ($name === 'email' && !$this->isValidEmail($value)) {
                $errors[$name] = 'Bitte geben Sie eine gültige E-Mail-Adresse ein, z. B. name@beispiel.de.';
                continue;
            }

            $data[$name] = $value;
        }

        return ['data' => $data, 'errors' => $errors];
    }

    /**
     * Normalisiert einen Wert. Gibt null zurück, wenn er kein gültiges UTF-8 ist.
     */
    private function clean(mixed $raw, bool $multiline): ?string
    {
        if (!is_scalar($raw)) {
            return null;
        }
        $value = (string) $raw;
        if (!mb_check_encoding($value, 'UTF-8')) {
            return null;
        }
        $value = str_replace(["\r\n", "\r"], "\n", $value);
        if ($multiline) {
            // Steuerzeichen außer Zeilenumbruch und Tab entfernen.
            $value = (string) preg_replace('/[^\P{C}\n\t]/u', '', $value);
            // Mehr als zwei Leerzeilen am Stück zusammenfassen.
            $value = (string) preg_replace("/\n{3,}/", "\n\n", $value);
        } else {
            $value = str_replace(["\n", "\t"], ' ', $value);
            $value = (string) preg_replace('/\p{C}/u', '', $value);
            $value = (string) preg_replace('/ {2,}/', ' ', $value);
        }
        return trim($value);
    }

    private function isValidEmail(string $email): bool
    {
        if (filter_var($email, FILTER_VALIDATE_EMAIL) === false) {
            return false;
        }
        // Domain muss einen Punkt enthalten (filter_var akzeptiert z. B. „a@localhost“ nicht immer zuverlässig).
        $domain = substr((string) strrchr($email, '@'), 1);
        return str_contains($domain, '.');
    }

    private function requiredMessage(string $name): string
    {
        return match ($name) {
            'name' => 'Bitte geben Sie Ihren Namen ein.',
            'email' => 'Bitte geben Sie Ihre E-Mail-Adresse ein.',
            'nachricht' => 'Bitte geben Sie Ihre Nachricht ein.',
            default => 'Bitte füllen Sie dieses Feld aus.',
        };
    }
}
