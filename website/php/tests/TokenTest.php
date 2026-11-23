<?php

declare(strict_types=1);

namespace Koenigshof\Kontakt\Tests;

use Koenigshof\Kontakt\Token;
use PHPUnit\Framework\TestCase;

final class TokenTest extends TestCase
{
    private Token $token;

    protected function setUp(): void
    {
        $this->token = new Token(str_repeat('x', 40));
    }

    public function testValidTokenAfterMinimumTime(): void
    {
        $t = $this->token->issue(1_800_000_000);
        self::assertSame(Token::VALID, $this->token->verify($t, 1_800_000_010, 3, 7200));
    }

    public function testTooFast(): void
    {
        $t = $this->token->issue(1_800_000_000);
        self::assertSame(Token::TOO_FAST, $this->token->verify($t, 1_800_000_001, 3, 7200));
    }

    public function testExpired(): void
    {
        $t = $this->token->issue(1_800_000_000);
        self::assertSame(Token::EXPIRED, $this->token->verify($t, 1_800_010_000, 3, 7200));
    }

    public function testTamperedTimestampIsInvalid(): void
    {
        $t = $this->token->issue(1_800_000_000);
        $forged = '1700000000' . substr($t, 10);
        self::assertSame(Token::INVALID, $this->token->verify($forged, 1_800_000_010, 3, 7200));
    }

    public function testTokenFromOtherSecretIsInvalid(): void
    {
        $other = (new Token(str_repeat('y', 40)))->issue(1_800_000_000);
        self::assertSame(Token::INVALID, $this->token->verify($other, 1_800_000_010, 3, 7200));
    }

    public function testGarbageIsInvalid(): void
    {
        foreach (['', 'abc', str_repeat('1', 500), '1.2.3', "1800000000.<script>.x"] as $garbage) {
            self::assertSame(Token::INVALID, $this->token->verify($garbage, 1_800_000_010, 3, 7200));
        }
    }

    public function testFutureTokenIsInvalid(): void
    {
        $t = $this->token->issue(1_800_000_100);
        self::assertSame(Token::INVALID, $this->token->verify($t, 1_800_000_000, 3, 7200));
    }
}
