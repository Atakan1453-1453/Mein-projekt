<?php

declare(strict_types=1);

namespace Koenigshof\Kontakt;

use PHPMailer\PHPMailer\Exception as MailException;
use PHPMailer\PHPMailer\PHPMailer;

/**
 * Baut die Benachrichtigungs-E-Mail und versendet sie über PHPMailer.
 *
 * Sicherheit:
 *  - Absender („From“) ist immer die konfigurierte Adresse der eigenen Domain
 *    (SPF/DKIM/DMARC-konform). Die Adresse der anfragenden Person steht nur
 *    in „Reply-To“.
 *  - Reine Text-E-Mail: Eingaben können kein HTML/JavaScript einschleusen.
 *  - Es wird KEINE Kopie/Bestätigung an die eingegebene Adresse geschickt –
 *    sonst ließe sich das Formular zum Versand von Spam an Dritte missbrauchen.
 */
final class Mailer
{
    private const LABELS = [
        'anliegen' => 'Anliegen',
        'name' => 'Name',
        'firma' => 'Firma',
        'email' => 'E-Mail',
        'telefon' => 'Telefon',
        'branche' => 'Branche / Sortiment',
        'flaeche' => 'Flächenbedarf (ca. m²)',
        'zeitraum' => 'Gewünschter Starttermin',
    ];

    public function __construct(private readonly Config $config)
    {
    }

    /** @param array<string, string> $data bereits validierte Daten */
    public function buildSubject(array $data): string
    {
        $topic = $this->topic($data['anliegen'] ?? '');
        $subject = sprintf('[%s] %s: %s', $this->config->siteName(), $topic['subject'] ?? 'Anfrage', $data['name'] ?? '');
        // Sicherheitsnetz gegen Header-Injection (Validator verhindert das bereits).
        return mb_substr(trim((string) preg_replace('/[\r\n]+/', ' ', $subject)), 0, 180);
    }

    /** @param array<string, string> $data */
    public function buildBody(array $data, \DateTimeImmutable $now): string
    {
        $topic = $this->topic($data['anliegen'] ?? '');
        $lines = ['Neue Anfrage über das Kontaktformular der Website', str_repeat('=', 50), ''];

        foreach (['anliegen', 'name', 'firma', 'email', 'telefon'] as $key) {
            $value = $key === 'anliegen' ? ($topic['label'] ?? '') : ($data[$key] ?? '');
            if ($value !== '') {
                $lines[] = str_pad(self::LABELS[$key] . ':', 12) . ' ' . $value;
            }
        }

        $rental = array_filter([
            'branche' => $data['branche'] ?? '',
            'flaeche' => $data['flaeche'] ?? '',
            'zeitraum' => $data['zeitraum'] ?? '',
        ], static fn (string $v): bool => $v !== '');
        if ($rental !== []) {
            $lines[] = '';
            $lines[] = 'Angaben zur Mietanfrage';
            $lines[] = str_repeat('-', 23);
            foreach ($rental as $key => $value) {
                $lines[] = self::LABELS[$key] . ': ' . $value;
            }
        }

        $lines[] = '';
        $lines[] = 'Nachricht';
        $lines[] = str_repeat('-', 9);
        $lines[] = $data['nachricht'] ?? '';
        $lines[] = '';
        $lines[] = '-- ';
        $lines[] = sprintf('Gesendet am %s Uhr über das Kontaktformular.', $now->format('d.m.Y \u\m H:i'));
        $lines[] = 'Mit „Antworten“ antworten Sie direkt der anfragenden Person.';

        return implode("\n", $lines) . "\n";
    }

    /**
     * Versendet die Nachricht.
     *
     * @param array<string, string> $data
     * @throws MailException|\RuntimeException
     */
    public function send(array $data, \DateTimeImmutable $now): void
    {
        $mail = new PHPMailer(true);
        $mail->CharSet = PHPMailer::CHARSET_UTF8;
        // 8bit (Standard); PHPMailer wechselt bei sehr langen Zeilen automatisch auf quoted-printable.
        $mail->Encoding = PHPMailer::ENCODING_8BIT;
        $mail->XMailer = ' '; // keine Versionsangabe im Header
        $mail->isHTML(false);

        $transport = $this->config->transport();
        if ($transport === 'smtp') {
            $smtp = $this->config->smtp();
            $mail->isSMTP();
            $mail->Host = $smtp['host'];
            $mail->Port = $smtp['port'];
            $mail->Timeout = $smtp['timeout'];
            $mail->SMTPAuth = $smtp['username'] !== '';
            $mail->Username = $smtp['username'];
            $mail->Password = $smtp['password'];
            $mail->SMTPSecure = match ($smtp['encryption']) {
                'ssl' => PHPMailer::ENCRYPTION_SMTPS,
                'none' => '',
                default => PHPMailer::ENCRYPTION_STARTTLS,
            };
            $mail->SMTPAutoTLS = $smtp['encryption'] !== 'none';
        } elseif ($transport === 'mail') {
            $mail->isMail();
        }

        $from = $this->config->from() !== '' ? $this->config->from() : 'website@localhost.test';
        $to = $this->config->recipient() !== '' ? $this->config->recipient() : 'empfang@localhost.test';
        $mail->setFrom($from, $this->config->fromName(), false);
        $mail->addAddress($to, $this->config->recipientName());
        $mail->addReplyTo($data['email'] ?? '', $data['name'] ?? '');
        $mail->Subject = $this->buildSubject($data);
        $mail->Body = $this->buildBody($data, $now);

        if ($transport === 'file') {
            // NUR für Entwicklung/Tests: Nachricht als .eml-Datei ablegen statt zu senden.
            $mail->preSend();
            $dir = $this->config->fileTransportDir();
            if (!is_dir($dir) && !@mkdir($dir, 0700, true) && !is_dir($dir)) {
                throw new \RuntimeException('Mail-Verzeichnis nicht beschreibbar.');
            }
            $file = sprintf('%s/%s-%s.eml', $dir, $now->format('Ymd-His'), bin2hex(random_bytes(4)));
            if (file_put_contents($file, $mail->getSentMIMEMessage()) === false) {
                throw new \RuntimeException('Mail-Datei konnte nicht geschrieben werden.');
            }
            return;
        }

        $mail->send();
    }

    /** @return array{value: string, label: string, subject: string}|array{} */
    private function topic(string $value): array
    {
        foreach ($this->config->topics() as $topic) {
            if ($topic['value'] === $value) {
                return $topic;
            }
        }
        return [];
    }
}
