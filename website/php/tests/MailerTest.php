<?php

declare(strict_types=1);

namespace Koenigshof\Kontakt\Tests;

use Koenigshof\Kontakt\Mailer;
use PHPUnit\Framework\TestCase;

final class MailerTest extends TestCase
{
    public function testFileTransportWritesSafeMessage(): void
    {
        $storage = sys_get_temp_dir() . '/kontakt-mail-' . bin2hex(random_bytes(4));
        $config = TestConfig::create([], $storage);
        $mailer = new Mailer($config);
        $data = TestConfig::validInput();
        unset($data['website']);

        $mailer->send($data, new \DateTimeImmutable('2026-11-23 13:05:00'));

        $files = glob($storage . '/mails/*.eml') ?: [];
        self::assertCount(1, $files);
        $eml = (string) file_get_contents($files[0]);

        // Absender = eigene Adresse, Antwort an die anfragende Person
        self::assertMatchesRegularExpression('/^From: .*<website@example\.de>/m', $eml);
        self::assertMatchesRegularExpression('/^Reply-To: .*<erika@example\.org>/m', $eml);
        self::assertMatchesRegularExpression('/^To: .*empfang@example\.de/m', $eml);
        // Nur Text, kein HTML
        self::assertStringContainsString('Content-Type: text/plain; charset=utf-8', $eml);
        self::assertStringNotContainsString('text/html', $eml);
        // Keine Kopie an die anfragende Person
        self::assertDoesNotMatchRegularExpression('/^(Cc|Bcc):/mi', $eml);

        $body = $eml;
        self::assertStringContainsString('Mietfläche / Vermietung', $body);
        self::assertStringContainsString('Angaben zur Mietanfrage', $body);
        self::assertStringContainsString('23.11.2026 um 13:05', $body);

        array_map('unlink', $files);
    }

    public function testSubjectHasNoLineBreaks(): void
    {
        $mailer = new Mailer(TestConfig::create());
        $subject = $mailer->buildSubject(['anliegen' => 'presse', 'name' => "Max\r\nBcc: x@example.com"]);
        self::assertStringNotContainsString("\n", $subject);
        self::assertStringNotContainsString("\r", $subject);
        self::assertStringStartsWith('[Galerie Königshof] Presse:', $subject);
    }
}
