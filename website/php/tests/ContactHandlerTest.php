<?php

declare(strict_types=1);

namespace Koenigshof\Kontakt\Tests;

use Koenigshof\Kontakt\Config;
use Koenigshof\Kontakt\ContactHandler;
use Koenigshof\Kontakt\RateLimiter;
use Koenigshof\Kontakt\SpamGuard;
use Koenigshof\Kontakt\Token;
use Koenigshof\Kontakt\Validator;
use PHPUnit\Framework\TestCase;

final class ContactHandlerTest extends TestCase
{
    private const NOW = 1_800_000_000;

    /** @var list<array<string, string>> */
    private array $sent = [];
    private Config $config;
    private Token $token;
    private bool $failSending = false;

    protected function setUp(): void
    {
        $this->config = TestConfig::create(['rate_limit' => ['max_requests' => 3]]);
        $this->token = new Token($this->config->secret());
        $this->sent = [];
    }

    private function handler(): ContactHandler
    {
        return new ContactHandler(
            $this->config,
            new Validator($this->config),
            new SpamGuard($this->config, $this->token),
            new RateLimiter($this->config->storageDir() . '/ratelimit', $this->config->secret(), $this->config->rateLimitMax(), 3600),
            $this->token,
            function (array $data): void {
                if ($this->failSending) {
                    throw new \RuntimeException('SMTP down');
                }
                $this->sent[] = $data;
            },
        );
    }

    /** @param array<string, string> $extra */
    private function server(array $extra = []): array
    {
        return $extra + [
            'REQUEST_METHOD' => 'POST',
            'HTTP_ACCEPT' => 'application/json',
            'HTTP_ORIGIN' => 'https://galeriekoenigshof.de',
            'HTTP_SEC_FETCH_SITE' => 'same-origin',
            'REMOTE_ADDR' => '203.0.113.' . random_int(1, 250),
            'CONTENT_LENGTH' => '800',
        ];
    }

    private function now(int $offset = 10): \DateTimeImmutable
    {
        return (new \DateTimeImmutable())->setTimestamp(self::NOW + $offset);
    }

    /** @return array<string, string> */
    private function input(): array
    {
        return ['token' => $this->token->issue(self::NOW)] + TestConfig::validInput();
    }

    public function testTokenEndpoint(): void
    {
        $res = $this->handler()->handle(['REQUEST_METHOD' => 'GET'], ['token' => '1'], [], $this->now());
        self::assertSame(200, $res->status);
        $data = json_decode($res->body, true);
        self::assertMatchesRegularExpression('/^\d+\.[a-f0-9]{24}\.[a-f0-9]{64}$/', $data['token']);
    }

    public function testValidSubmissionIsSent(): void
    {
        $res = $this->handler()->handle($this->server(), [], $this->input(), $this->now());
        self::assertSame(200, $res->status, $res->body);
        self::assertTrue(json_decode($res->body, true)['ok']);
        self::assertCount(1, $this->sent);
    }

    public function testNoJsSubmissionRedirects(): void
    {
        $input = TestConfig::validInput(); // ohne Token
        $res = $this->handler()->handle($this->server(['HTTP_ACCEPT' => 'text/html']), [], $input, $this->now());
        self::assertSame(303, $res->status);
        self::assertSame('/kontakt/danke/', $res->headers['Location']);
        self::assertCount(1, $this->sent);
    }

    public function testNoJsValidationErrorRedirectsToErrorPage(): void
    {
        $res = $this->handler()->handle($this->server(['HTTP_ACCEPT' => 'text/html']), [], ['name' => 'x'], $this->now());
        self::assertSame(303, $res->status);
        self::assertSame('/kontakt/fehler/', $res->headers['Location']);
        self::assertCount(0, $this->sent);
    }

    public function testHoneypotSilentlyDropped(): void
    {
        $input = ['website' => 'https://spam.example'] + $this->input();
        $res = $this->handler()->handle($this->server(), [], $input, $this->now());
        self::assertSame(200, $res->status, 'Bot soll „Erfolg“ sehen');
        self::assertCount(0, $this->sent, 'aber nichts wird gesendet');
    }

    public function testTooFastIsRejected(): void
    {
        $res = $this->handler()->handle($this->server(), [], $this->input(), $this->now(1));
        self::assertSame(400, $res->status);
        self::assertCount(0, $this->sent);
    }

    public function testForgedTokenIsRejected(): void
    {
        $input = ['token' => '1800000000.' . str_repeat('a', 24) . '.' . str_repeat('b', 64)] + TestConfig::validInput();
        $res = $this->handler()->handle($this->server(), [], $input, $this->now());
        self::assertSame(400, $res->status);
    }

    public function testRequireTokenRejectsMissingToken(): void
    {
        $this->config = TestConfig::create(['require_token' => true]);
        $this->token = new Token($this->config->secret());
        $res = $this->handler()->handle($this->server(), [], TestConfig::validInput(), $this->now());
        self::assertSame(400, $res->status);
    }

    public function testCrossSiteSubmissionIsRejected(): void
    {
        $res = $this->handler()->handle($this->server(['HTTP_ORIGIN' => 'https://evil.example']), [], $this->input(), $this->now());
        self::assertSame(403, $res->status);

        $res = $this->handler()->handle($this->server(['HTTP_SEC_FETCH_SITE' => 'cross-site']), [], $this->input(), $this->now());
        self::assertSame(403, $res->status);
        self::assertCount(0, $this->sent);
    }

    public function testRateLimit(): void
    {
        $server = $this->server(['REMOTE_ADDR' => '198.51.100.9']);
        for ($i = 0; $i < 3; $i++) {
            self::assertSame(200, $this->handler()->handle($server, [], $this->input(), $this->now())->status);
        }
        $res = $this->handler()->handle($server, [], $this->input(), $this->now());
        self::assertSame(429, $res->status);
        self::assertSame('600', $res->headers['Retry-After']);
    }

    public function testTooManyLinks(): void
    {
        $input = ['nachricht' => 'Kaufen Sie hier: https://a.example https://b.example www.c.example'] + $this->input();
        $res = $this->handler()->handle($this->server(), [], $input, $this->now());
        self::assertSame(422, $res->status);
        self::assertArrayHasKey('nachricht', json_decode($res->body, true)['errors']);
    }

    public function testOversizedRequest(): void
    {
        $res = $this->handler()->handle($this->server(['CONTENT_LENGTH' => '999999']), [], $this->input(), $this->now());
        self::assertSame(413, $res->status);
    }

    public function testOnlyPostAllowed(): void
    {
        $res = $this->handler()->handle(['REQUEST_METHOD' => 'PUT'], [], [], $this->now());
        self::assertSame(405, $res->status);
    }

    public function testMailFailureReturns500WithoutLeakingDetails(): void
    {
        $this->failSending = true;
        $errorLog = ini_get('error_log');
        ini_set('error_log', sys_get_temp_dir() . '/kontakt-test-error.log');
        try {
            $res = $this->handler()->handle($this->server(), [], $this->input(), $this->now());
        } finally {
            ini_set('error_log', (string) $errorLog);
        }
        self::assertSame(500, $res->status);
        self::assertStringNotContainsString('SMTP down', $res->body);
    }
}
