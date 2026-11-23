<?php

declare(strict_types=1);

namespace Koenigshof\Kontakt\Tests;

use Koenigshof\Kontakt\Validator;
use PHPUnit\Framework\TestCase;

final class ValidatorTest extends TestCase
{
    private Validator $validator;

    protected function setUp(): void
    {
        $this->validator = new Validator(TestConfig::create());
    }

    public function testValidInputPasses(): void
    {
        $result = $this->validator->validate(TestConfig::validInput());
        self::assertSame([], $result['errors']);
        self::assertSame('Erika Mustermann', $result['data']['name']);
        self::assertSame('Damenmode', $result['data']['branche']);
        self::assertArrayNotHasKey('website', $result['data'], 'Honeypot darf nicht in den Daten landen');
    }

    public function testRequiredFields(): void
    {
        $result = $this->validator->validate([]);
        self::assertArrayHasKey('anliegen', $result['errors']);
        self::assertArrayHasKey('name', $result['errors']);
        self::assertArrayHasKey('email', $result['errors']);
        self::assertArrayHasKey('nachricht', $result['errors']);
        self::assertArrayNotHasKey('telefon', $result['errors']);
        self::assertArrayNotHasKey('firma', $result['errors']);
    }

    public function testUnknownTopicIsRejected(): void
    {
        $input = ['anliegen' => 'hacking'] + TestConfig::validInput();
        self::assertArrayHasKey('anliegen', $this->validator->validate($input)['errors']);
    }

    public function testRentalFieldsAreDroppedForOtherTopics(): void
    {
        $input = ['anliegen' => 'presse'] + TestConfig::validInput();
        $result = $this->validator->validate($input);
        self::assertSame([], $result['errors']);
        self::assertArrayNotHasKey('branche', $result['data']);
        self::assertArrayNotHasKey('flaeche', $result['data']);
    }

    /** @return iterable<string, array{string}> */
    public static function invalidEmails(): iterable
    {
        yield 'ohne @' => ['erika.example.org'];
        yield 'ohne Domain-Punkt' => ['erika@localhost'];
        yield 'Leerzeichen' => ['erika @example.org'];
        yield 'Header-Injection' => ["erika@example.org\nBcc: opfer@example.com"];
        yield 'Header-Injection CR' => ["erika@example.org\r\nBcc: opfer@example.com"];
    }

    #[\PHPUnit\Framework\Attributes\DataProvider('invalidEmails')]
    public function testInvalidEmailsAreRejected(string $email): void
    {
        $input = ['email' => $email] + TestConfig::validInput();
        self::assertArrayHasKey('email', $this->validator->validate($input)['errors']);
    }

    public function testNameWithNewlineIsRejected(): void
    {
        $input = ['name' => "Erika\r\nBcc: opfer@example.com"] + TestConfig::validInput();
        self::assertArrayHasKey('name', $this->validator->validate($input)['errors']);
    }

    public function testLengthIsCountedInCharactersNotBytes(): void
    {
        // 20 Umlaute = 40 Bytes, aber genau 20 Zeichen → gültig
        $input = ['nachricht' => str_repeat('ä', 20)] + TestConfig::validInput();
        self::assertArrayNotHasKey('nachricht', $this->validator->validate($input)['errors']);

        $input = ['nachricht' => str_repeat('ä', 19)] + TestConfig::validInput();
        self::assertArrayHasKey('nachricht', $this->validator->validate($input)['errors']);
    }

    public function testTooLongMessage(): void
    {
        $input = ['nachricht' => str_repeat('x', 5001)] + TestConfig::validInput();
        self::assertArrayHasKey('nachricht', $this->validator->validate($input)['errors']);
    }

    public function testInvalidUtf8IsRejected(): void
    {
        $input = ['name' => "Erika \xC3\x28"] + TestConfig::validInput();
        self::assertArrayHasKey('name', $this->validator->validate($input)['errors']);
    }

    public function testArrayInjectionIsRejected(): void
    {
        $input = ['name' => ['a', 'b']] + TestConfig::validInput();
        self::assertArrayHasKey('name', $this->validator->validate($input)['errors']);
    }

    public function testControlCharactersAreStripped(): void
    {
        $input = ['nachricht' => "Hallo\x00\x07 Welt,\n\n\n\n\nwir haben eine Frage zur Fläche."] + TestConfig::validInput();
        $result = $this->validator->validate($input);
        self::assertSame("Hallo Welt,\n\nwir haben eine Frage zur Fläche.", $result['data']['nachricht']);
    }

    public function testPhonePattern(): void
    {
        $input = ['telefon' => '0211 / 12 34 56'] + TestConfig::validInput();
        self::assertArrayNotHasKey('telefon', $this->validator->validate($input)['errors']);

        $input = ['telefon' => 'ruf mich an'] + TestConfig::validInput();
        self::assertArrayHasKey('telefon', $this->validator->validate($input)['errors']);
    }

    public function testHtmlIsKeptAsPlainText(): void
    {
        // Kein HTML-Escaping nötig: Die Mail ist reiner Text. Wert bleibt unverändert erhalten.
        $input = ['nachricht' => '<script>alert(1)</script> bitte um Rückruf zur Fläche'] + TestConfig::validInput();
        $result = $this->validator->validate($input);
        self::assertSame('<script>alert(1)</script> bitte um Rückruf zur Fläche', $result['data']['nachricht']);
    }
}
